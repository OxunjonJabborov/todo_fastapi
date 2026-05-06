import asyncio
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import security
from database import Base, get_db
from enums import Roles
from main import app
from models import User

TestSession = None


async def override_get_db():
    if TestSession is None:
        raise RuntimeError("Test session sozlanmagan.")

    async with TestSession() as session:
        yield session


class TodoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global TestSession

        cls.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestSession = async_sessionmaker(
            bind=cls.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        asyncio.run(cls._init_db())
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        asyncio.run(cls.engine.dispose())

    @classmethod
    async def _init_db(cls):
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSession() as session:
            admin = User(
                username="admin",
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                hashed_password=security.get_password_hash("secret1"),
                role=Roles.ADMIN.value,
            )
            session.add(admin)
            await session.commit()

    def test_admin_can_create_and_delete_todo(self):
        login = self.client.post(
            "/users/login",
            data={"username": "admin", "password": "secret1"},
        )
        self.assertEqual(login.status_code, 200, login.text)

        token = login.json()["access_token"]
        create = self.client.post(
            "/todo/",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Smoke", "description": "Test"},
        )
        self.assertEqual(create.status_code, 200, create.text)
        data = create.json()
        self.assertEqual(data["name"], "Smoke")
        self.assertEqual(data["user_id"], 1)
        self.assertFalse(data["is_completed"])

        delete = self.client.delete(f"/todo/{data['id']}")
        self.assertEqual(delete.status_code, 200, delete.text)
