import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Definimos os caminhos automaticamente para as outras pastas
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "freeflow.db"
SCHEMAS_PATH = Path(__file__).parent / "schemas.sql"
SEED_PATH = Path(__file__).parent / "seed.sql"


class DatabaseConnection:
    def __init__(self):
        # Estamos criando a pasta (se ela não existe) onde a nossa base de dados ficará
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Chamamos o SQLite para conectar-se com a base de dados, caso não existir ela é criada
        self.conn = sqlite3.connect(DB_PATH)

        # Estamos avisando para o SQLite que queremos que os dados pegos com Querys se comportem como dicionário
        self.conn.row_factory = sqlite3.Row

        # Por questão de compatibilidade, a verificação de chaves estrangeiras vem desligada, estamos ligando-a
        self.conn.execute("PRAGMA foreign_key = ON")

    def initialize_schema(self):
        """
        Lê e execute o arquivo 'schemas.sql' para criar
        as tabelas conforme definido na modelagem DER.
        """
        with open(SCHEMAS_PATH, "r", encoding="utf-8") as f:
            # Estamos executando todos os CREATE TABLE ... de uma vez
            self.conn.executescript(f.read())
        # Com o comando abaixo estamos confirmando as alterações dentro do arquivo do banco de dados
        self.conn.commit()

    def seed_data(self):
        """
        Lê e executa o arquivo seed.sql para popular
        as bases de dados, apenas se o banco estiver
        vazio
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        if cursor.fetchone()[0] == 0:
            with open(SEED_PATH, "r", encoding="utf-8") as f:
                self.conn.executescript(f.read())
            self.conn.commit()
            print("Dados de exemplos inseridos!")

    @contextmanager
    def get_cursor(self):
        """
        Context Manager para garantir que o cursor
        seja fechado corretamente
        """

        cursor = self.conn.cursor()

        try:
            yield cursor  # Quando chamarmos o cursor, o try vai ficar pausado até que termine o uso externo
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def close(self):
        self.conn.close()
