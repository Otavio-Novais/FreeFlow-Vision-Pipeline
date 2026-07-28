import unittest
import os
from pathlib import Path
from src.database.repository import TransactionRepository


class TestTransactionRepository(unittest.TestCase):
    """
    Testes unitários para o TransactionRepository do Free Flow.
    Cobre todos os cenários de negócio: normal, divergências e sem tag.
    """

    @classmethod
    def setUpClass(cls):
        """
        Configuração inicial: remove banco anterior para garantir testes limpos.
        """
        # Remove banco anterior se existir (para testes isolados)
        db_path = Path('data/freeflow.db')
        if db_path.exists():
            db_path.unlink()
        
        cls.repo = TransactionRepository()

    @classmethod
    def tearDownClass(cls):
        """Fecha a conexão após todos os testes."""
        cls.repo.close()

    def test_01_transacao_normal_com_tag(self):
        """
        Cenário 1: Transação normal - placa e tag batem perfeitamente.
        Esperado: Status PENDING, valor R$ 5.50 (Categoria 1 - carro)
        """
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='IYJ7F53',           # Placa cadastrada na tag OBO-002
            vehicle_detected='carro',
            plate_confidence=0.98,
            vehicle_confidence=0.95,
            obo_tag_number='OBO-002'
        )

        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['plate_read'], 'IYJ7F53')
        self.assertEqual(result['vehicle_detected'], 'carro')
        self.assertAlmostEqual(result['toll_amount'], 5.50)
        self.assertIsNone(result['divergence_reason'])
        self.assertIsNotNone(result['transaction_id'])
        print(f"✅ Teste 1 passou: Transação normal registrada (ID: {result['transaction_id']})")

    def test_02_divergencia_de_placa(self):
        """
        Cenário 2: Divergência de placa - OCR leu placa diferente da cadastrada na tag.
        Esperado: Status DIVERGENCE com motivo explicando a diferença.
        """
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='XYZ9999',           # Placa ERRADA (tag é de IYJ7F53)
            vehicle_detected='carro',
            plate_confidence=0.85,
            vehicle_confidence=0.90,
            obo_tag_number='OBO-002'
        )

        self.assertEqual(result['status'], 'DIVERGENCE')
        self.assertIn('XYZ9999', result['divergence_reason'])
        self.assertIn('IYJ7F53', result['divergence_reason'])
        print(f"✅ Teste 2 passou: Divergência de placa detectada")
        print(f"   Motivo: {result['divergence_reason']}")

    def test_03_divergencia_de_categoria(self):
        """
        Cenário 3: Divergência de categoria - Caminhão usando tag de carro (fraude).
        Esperado: Status DIVERGENCE com motivo sobre categoria.
        """
        result = self.repo.register_transaction(
            gate_id=3,
            plate_read='TRK1234',           # Placa do caminhão
            vehicle_detected='caminhao_medio',  # YOLO detectou caminhão
            plate_confidence=0.99,
            vehicle_confidence=0.97,
            obo_tag_number='OBO-001'        # Tag do João (vinculada a carro ABC1234)
        )

        self.assertEqual(result['status'], 'DIVERGENCE')
        self.assertIn('caminhao_medio', result['divergence_reason'])
        print(f"✅ Teste 3 passou: Divergência de categoria detectada (fraude)")
        print(f"   Motivo: {result['divergence_reason']}")

    def test_04_veiculo_sem_tag_unregistered(self):
        """
        Cenário 4: Veículo sem tag OBO - fluxo de cobrança por notificação.
        Esperado: Status UNREGISTERED.
        """
        result = self.repo.register_transaction(
            gate_id=2,
            plate_read='GHI5678',           # Carro sem tag cadastrada
            vehicle_detected='carro',
            plate_confidence=0.92,
            vehicle_confidence=0.88,
            obo_tag_number=None             # Sem tag
        )

        self.assertEqual(result['status'], 'UNREGISTERED')
        self.assertEqual(result['plate_read'], 'GHI5678')
        self.assertAlmostEqual(result['toll_amount'], 5.50)
        print(f"✅ Teste 4 passou: Veículo sem tag registrado para cobrança via boleto")

    def test_05_tag_inativa(self):
        """
        Cenário 5: Tag OBO inativa (is_active = 0).
        Esperado: Status UNREGISTERED com motivo de tag inativa.
        """
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='ABC1234',
            vehicle_detected='carro',
            plate_confidence=0.95,
            vehicle_confidence=0.93,
            obo_tag_number='OBO-005'        # Tag inativa do João
        )

        self.assertEqual(result['status'], 'UNREGISTERED')
        self.assertIn('inativa', result['divergence_reason'].lower())
        print(f"✅ Teste 5 passou: Tag inativa detectada")
        print(f"   Motivo: {result['divergence_reason']}")

    def test_06_veiculo_nao_cadastrado(self):
        """
        Cenário 6: Tag existe, mas veículo não está no cadastro (AUDIT).
        Para testar isso, precisaríamos de uma tag sem vehicle_id, 
        mas como nosso seed não tem esse caso, vamos simular com tag inexistente.
        """
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='ABC1234',
            vehicle_detected='carro',
            plate_confidence=0.90,
            vehicle_confidence=0.85,
            obo_tag_number='OBO-999'        # Tag que não existe
        )

        self.assertEqual(result['status'], 'UNREGISTERED')
        print(f"✅ Teste 6 passou: Tag inexistente tratada como UNREGISTERED")

    def test_07_categoria_desconhecida(self):
        """
        Cenário 7: YOLO detectou tipo de veículo não mapeado nas categorias.
        Esperado: toll_amount = 0.0, category_id = None.
        """
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='ABC1234',
            vehicle_detected='bicicleta',   # Tipo não mapeado
            plate_confidence=0.80,
            vehicle_confidence=0.70,
            obo_tag_number=None
        )

        self.assertEqual(result['status'], 'UNREGISTERED')
        self.assertEqual(result['toll_amount'], 0.0)
        print(f"✅ Teste 7 passou: Categoria desconhecida tratada (valor R$ 0,00)")

    def test_08_get_divergences(self):
        """
        Testa o método de consulta de divergências.
        Esperado: Retornar lista com as transações de divergência registradas.
        """
        divergences = self.repo.get_divergences(limit=10)
        
        self.assertIsInstance(divergences, list)
        self.assertGreater(len(divergences), 0)
        
        # Verifica se as divergências têm os campos esperados
        first_div = divergences[0]
        self.assertIn('id', first_div)
        self.assertIn('plate_read', first_div)
        self.assertIn('status', first_div)
        self.assertIn('divergence_reason', first_div)
        self.assertIn('gate_code', first_div)
        
        print(f"✅ Teste 8 passou: {len(divergences)} divergências encontradas para auditoria")
        for div in divergences[:3]:  # Mostra as 3 primeiras
            print(f"   - {div['plate_read']} | {div['status']} | {div['gate_code']}")

    def test_09_get_daily_revenue(self):
        """
        Testa o método de faturamento diário.
        Esperado: Retornar dicionário com totais de transações e receitas por status.
        """
        revenue = self.repo.get_daily_revenue()
        
        self.assertIsInstance(revenue, dict)
        self.assertIn('total_transactions', revenue)
        self.assertIn('revenue_pending', revenue)
        self.assertIn('revenue_divergence', revenue)
        self.assertIn('revenue_unregistered', revenue)
        
        self.assertGreater(revenue['total_transactions'], 0)
        
        print(f"✅ Teste 9 passou: Faturamento do dia calculado")
        print(f"   Total de transações: {revenue['total_transactions']}")
        print(f"   Receita Pendente: R$ {revenue['revenue_pending']:.2f}")
        print(f"   Receita Divergência: R$ {revenue['revenue_divergence']:.2f}")
        print(f"   Receita Não Registrada: R$ {revenue['revenue_unregistered']:.2f}")

    def test_10_multiples_transactions_same_plate(self):
        """
        Cenário 10: Múltiplas passagens do mesmo veículo no mesmo dia.
        Esperado: Todas registradas com IDs diferentes.
        """
        results = []
        for i in range(3):
            result = self.repo.register_transaction(
                gate_id=1,
                plate_read='IYJ7F53',
                vehicle_detected='carro',
                plate_confidence=0.95,
                vehicle_confidence=0.95,
                obo_tag_number='OBO-002'
            )
            results.append(result)

        # Verifica se todos têm IDs únicos
        transaction_ids = [r['transaction_id'] for r in results]
        self.assertEqual(len(transaction_ids), len(set(transaction_ids)))
        
        # Todos devem ser PENDING
        for r in results:
            self.assertEqual(r['status'], 'PENDING')
        
        print(f"✅ Teste 10 passou: 3 transações do mesmo veículo registradas com IDs únicos")


class TestEdgeCases(unittest.TestCase):
    """
    Testes de casos extremos e validação de entrada.
    """

    @classmethod
    def setUpClass(cls):
        cls.repo = TransactionRepository()

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    def test_placa_vazia(self):
        """Testa comportamento com placa vazia."""
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='',
            vehicle_detected='carro',
            plate_confidence=0.0,
            vehicle_confidence=0.0,
            obo_tag_number=None
        )
        # Deve registrar mesmo com placa vazia (status UNREGISTERED)
        self.assertEqual(result['status'], 'UNREGISTERED')
        print(f"✅ Teste edge case passou: Placa vazia tratada")

    def test_confidence_zero(self):
        """Testa comportamento com confiança zero."""
        result = self.repo.register_transaction(
            gate_id=1,
            plate_read='ABC1234',
            vehicle_detected='carro',
            plate_confidence=0.0,
            vehicle_confidence=0.0,
            obo_tag_number=None
        )
        self.assertEqual(result['status'], 'UNREGISTERED')
        print(f"✅ Teste edge case passou: Confiança zero tratada")


if __name__ == '__main__':
    # Executa os testes com verbose
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)