import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import connection as db_conn


class TestDatabaseConnectionInit(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    def test_directory_created_if_missing(self):
        import shutil

        shutil.rmtree(self.tmp_dir)
        db = db_conn.DatabaseConnection()
        self.assertTrue(self.tmp_db.parent.exists())
        db.close()

    def test_row_factory_set_to_row(self):
        db = db_conn.DatabaseConnection()
        self.assertEqual(db.conn.row_factory, db_conn.sqlite3.Row)
        db.close()

    def test_foreign_keys_pragma_called(self):
        db = db_conn.DatabaseConnection()
        cursor = db.conn.execute("PRAGMA foreign_keys")
        self.assertEqual(cursor.fetchone()[0], 0)
        db.close()


class TestDatabaseConnectionSchema(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()
        self.db = db_conn.DatabaseConnection()

    def tearDown(self):
        self.db.close()
        self._patcher.stop()

    def test_all_tables_created(self):
        self.db.initialize_schema()
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        expected = [
            "accounts",
            "obo_tags",
            "toll_categories",
            "toll_gates",
            "transactions",
            "vehicles",
        ]
        for table in expected:
            self.assertIn(table, tables)

    def test_indexes_created(self):
        self.db.initialize_schema()
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        expected_indexes = [
            "idx_obo_tags_tag_number",
            "idx_transactions_plate",
            "idx_transactions_status",
            "idx_transactions_timestamp",
            "idx_vehicles_plate",
        ]
        for idx in expected_indexes:
            self.assertIn(idx, indexes)

    def test_initialize_schema_idempotent(self):
        self.db.initialize_schema()
        self.db.initialize_schema()
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("transactions", tables)


class TestDatabaseConnectionSeed(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()
        self.db = db_conn.DatabaseConnection()
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()
        self._patcher.stop()

    def test_seed_inserts_toll_categories(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM toll_categories")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5)

    def test_seed_inserts_gates(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM toll_gates")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 3)

    def test_seed_inserts_accounts(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 3)

    def test_seed_inserts_vehicles(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5)

    def test_seed_inserts_obo_tags(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM obo_tags")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5)

    def test_seed_inserts_transactions(self):
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 4)

    def test_seed_data_idempotent(self):
        self.db.seed_data()
        self.db.seed_data()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM toll_categories")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 5)


class TestDatabaseConnectionGetCursor(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()
        self.db = db_conn.DatabaseConnection()
        self.db.initialize_schema()
        self.db.seed_data()

    def tearDown(self):
        self.db.close()
        self._patcher.stop()

    def test_commit_on_successful_cursor_usage(self):
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts (owner_name, cpf_cnpj) VALUES (?, ?)",
                ("Test User", "111.222.333-44"),
            )
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT owner_name FROM accounts WHERE cpf_cnpj = ?", ("111.222.333-44",)
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["owner_name"], "Test User")

    def test_rollback_on_exception(self):
        with self.assertRaises(ValueError):
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO accounts (owner_name, cpf_cnpj) VALUES (?, ?)",
                    ("Rollback User", "999.888.777-66"),
                )
                raise ValueError("Simulated error")
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM accounts WHERE cpf_cnpj = ?", ("999.888.777-66",)
        )
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_cursor_closed_after_context(self):
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        with self.assertRaises(Exception):
            cursor.execute("SELECT 1")


class TestDatabaseConnectionClose(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()
        self.db = db_conn.DatabaseConnection()

    def tearDown(self):
        self._patcher.stop()

    def test_close_cleans_up(self):
        self.db.close()
        with self.assertRaises(Exception):
            self.db.conn.execute("SELECT 1")


class TestTransactionsForeignKeyIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_db = Path(self.tmp_dir) / "test.db"
        self._patcher = patch.object(db_conn, "DB_PATH", self.tmp_db)
        self._patcher.start()
        self.db = db_conn.DatabaseConnection()
        self.db.initialize_schema()
        self.db.seed_data()

    def tearDown(self):
        self.db.close()
        self._patcher.stop()

    def test_transaction_references_gate(self):
        with self.db.get_cursor() as cursor:
            cursor.execute("""INSERT INTO transactions
                (timestamp, gate_id, plate_read, vehicle_detected, status)
                VALUES (datetime('now'), 1, 'ABC1234', 'carro', 'PENDING')""")
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT g.gate_code FROM transactions t "
            "JOIN toll_gates g ON t.gate_id = g.id WHERE t.plate_read = 'ABC1234'"
        )
        row = cursor.fetchone()
        self.assertEqual(row["gate_code"], "PORT-ANH-01")


if __name__ == "__main__":
    unittest.main()
