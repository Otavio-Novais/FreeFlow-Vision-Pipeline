from datetime import datetime
from typing import Optional

from .connection import DatabaseConnection


class TransactionRepository:
    def __init__(self):
        self.db = DatabaseConnection()
        self.db.initialize_schema()
        self.db.seed_data()

    def register_transaction(
        self,
        gate_id: int,
        plate_read: str,
        vehicle_detected: str,
        plate_confidence: float,
        vehicle_confidence: float,
        obo_tag_number: Optional[str] = None,
    ) -> dict:
        """
        Registra uma transação de passagem no Free Flow.
        Realiza o cruzamento entre placa lida e tag OBO para identificar divergências.

        Returns:
            dict com status da transação e detalhes
        """

        with self.db.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, base_price FROM toll_categories WHERE vehicle_type = ?",
                (vehicle_detected,),
            )

            category = cursor.fetchone()

            category_id = category["id"] if category else None
            toll_amount = category["base_price"] if category else 0.0

            cursor.execute(
                "SELECT id, category_id FROM vehicles WHERE plate = ?", (plate_read,)
            )
            existing_vehicle = cursor.fetchone()

            if existing_vehicle:
                # Veículo já existe, apenas atualiza a categoria se mudou
                if category_id and existing_vehicle["category_id"] != category_id:
                    cursor.execute(
                        "UPDATE vehicles SET category_id = ? WHERE plate = ?",
                        (category_id, plate_read),
                    )
                    print(
                        f"  🔄 Categoria do veículo {plate_read} atualizada para {vehicle_detected}"
                    )
            else:
                # Veículo não existe, cria novo registro
                cursor.execute(
                    """
                    INSERT INTO vehicles (plate, category_id, brand, model, year)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        plate_read,
                        category_id,
                        "Desconhecida",  # Não sabemos a marca ainda
                        "Desconhecido",  # Não sabemos o modelo ainda
                        None,  # Não sabemos o ano ainda
                    ),
                )
                print(
                    f"  🆕 Novo veículo cadastrado automaticamente: {plate_read} ({vehicle_detected})"
                )

            obo_tag_id = None
            tag = None
            divergence_reason = None
            status = "PENDING"

            if obo_tag_number:
                cursor.execute(
                    "SELECT id, vehicle_id FROM obo_tags WHERE tag_number = ? AND is_active = 1",
                    (obo_tag_number,),
                )
                tag = cursor.fetchone()

            if tag:
                obo_tag_id = tag["id"]

                cursor.execute(
                    "SELECT plate, category_id FROM vehicles WHERE id = ?",
                    (tag["vehicle_id"],),
                )
                registered_vehicle = cursor.fetchone()

                if registered_vehicle:
                    if registered_vehicle["plate"] != plate_read:
                        # Divergência! Placa lida diferente da tag
                        status = "DIVERGENCE"
                        divergence_reason = f"Placa lida ({plate_read}) difere da placa cadastrada na tag ({registered_vehicle['plate']})"

                    # Verifica se a categoria do YOLO bate com a categoria do veículo cadastrado
                    if category_id and registered_vehicle["category_id"] != category_id:
                        cursor.execute(
                            "SELECT name FROM toll_categories WHERE id = ?",
                            (registered_vehicle["category_id"],),
                        )

                        registered_cat = cursor.fetchone()

                        if registered_cat:
                            if divergence_reason:
                                divergence_reason += f"; Categoria YOLO ({vehicle_detected})  diferente da cadastrada ({registered_cat['name']})"
                            else:
                                status = "DIVERGENCE"
                                divergence_reason = f"Categoria YOLO ({vehicle_detected}) diferente da cadastrada ({registered_cat['name']})"
                else:
                    # TAG existe mas veículo não está cadastrado
                    status = "AUDIT"
                    divergence_reason = (
                        "Tag OBO ativa, mas veículo não encontrado no cadastro"
                    )
            else:
                # Tag não encontrada ou inativa
                status = "UNREGISTERED"
                divergence_reason = (
                    f"Tag OBO {obo_tag_number} não encontrada ou inativa"
                )

            # Inserimos a transação
            cursor.execute(
                """
            INSERT INTO transactions 
            (timestamp, gate_id, plate_read, plate_confidence, vehicle_detected, 
             vehicle_confidence, category_id, toll_amount, obo_tag_id, status, divergence_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    gate_id,
                    plate_read,
                    plate_confidence,
                    vehicle_detected,
                    vehicle_confidence,
                    category_id,
                    toll_amount,
                    obo_tag_id,
                    status,
                    divergence_reason,
                ),
            )

            transaction_id = cursor.lastrowid

            return {
                "transaction_id": transaction_id,
                "status": status,
                "plate_read": plate_read,
                "vehicle_detected": vehicle_detected,
                "toll_amount": toll_amount,
                "divergence_reason": divergence_reason,
            }

    def get_divergences(self, limit: int = 10) -> list:
        """
        Retorna transações com divergências para auditoria
        """

        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT t.id, t.timestamp, t.plate_read, t.vehicle_detected,
                        t.status, t.divergence_reason, t.toll_amount,
                        g.gate_code, g.location
                FROM transactions t
                JOIN toll_gates g ON t.gate_id = g.id
                WHERE t.status IN ('DIVERGENCE', 'AUDIT', 'UNREGISTERED')
                ORDER BY t.timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_daily_revenue(self, date: Optional[str] = None) -> dict:

        with self.db.get_cursor() as cursor:

            if date:
                cursor.execute(
                    """
                    SELECT COUNT(*) as total_transactions,
                        SUM(CASE WHEN status = 'PENDING' THEN toll_amount ELSE 0 END) as revenue_pending,
                        SUM(CASE WHEN status = 'DIVERGENCE' THEN toll_amount ELSE 0 END) as revenue_divergence,
                        SUM(CASE WHEN status = 'UNREGISTERED' THEN toll_amount ELSE 0 END) as revenue_unregistered
                    FROM transactions
                    WHERE DATE(timestamp) = ?
                """,
                    (date,),
                )
            else:
                cursor.execute("""
                    SELECT COUNT(*) as total_transactions,
                        SUM(CASE WHEN status = 'PENDING' THEN toll_amount ELSE 0 END) as revenue_pending,
                        SUM(CASE WHEN status = 'DIVERGENCE' THEN toll_amount ELSE 0 END) as revenue_divergence,
                        SUM(CASE WHEN status = 'UNREGISTERED' THEN toll_amount ELSE 0 END) as revenue_unregistered
                    FROM transactions
                    WHERE DATE(timestamp) = DATE('now')
                """)

            return dict(cursor.fetchone())

    def close(self):
        """
        Método de delegação: fecha a conexão do banco de dados.
        Isso permite que quem usa o Repositório não precise saber
        que existe um objeto 'db' interno.
        """
        self.db.close()
