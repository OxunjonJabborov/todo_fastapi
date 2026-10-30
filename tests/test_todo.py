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

    def _auth(self, username="admin", password="secret1"):
        login = self.client.post(
            "/users/login",
            data={"username": username, "password": password},
        )
        self.assertEqual(login.status_code, 200, login.text)
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    def _create_user(self, username):
        return self.client.post(
            "/users/user",
            json={
                "first_name": "Ali",
                "last_name": "Valiyev",
                "email": f"{username}@example.com",
                "username": username,
                "password": "secret1",
            },
        )

    def test_todo_get_update_list(self):
        headers = self._auth()
        todo_id = self.client.post(
            "/todo/", headers=headers, json={"name": "A", "description": "B"},
        ).json()["id"]

        update = self.client.put(
            f"/todo/{todo_id}",
            json={"name": "A2", "description": "B2", "is_completed": True},
        )
        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(update.json()["name"], "A2")
        self.assertTrue(update.json()["is_completed"])

        get = self.client.get(f"/todo/{todo_id}")
        self.assertEqual(get.json()["description"], "B2")

        todos = self.client.get("/todo/todos")
        self.assertIn(todo_id, [t["id"] for t in todos.json()])

    def test_missing_todo_returns_404(self):
        for response in (
            self.client.get("/todo/9999"),
            self.client.put("/todo/9999", json={"name": "x", "description": "y"}),
            self.client.delete("/todo/9999"),
        ):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["detail"], "9999 - raqamli todo topilmadi...")

    def test_create_todo_requires_admin(self):
        self.assertEqual(self._create_user("oddiy").status_code, 200)
        response = self.client.post(
            "/todo/", headers=self._auth("oddiy"), json={"name": "A", "description": "B"},
        )
        self.assertEqual(response.status_code, 403)

    def test_user_registration_and_profile(self):
        created = self._create_user("yangi")
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["role"], "user")
        self.assertNotIn("password", created.json())

        self.assertEqual(self._create_user("yangi").status_code, 400)

        same_email = self._create_user("boshqa")
        self.assertEqual(same_email.status_code, 200)
        duplicate_email = self.client.post(
            "/users/user",
            json={
                "first_name": "A", "last_name": "B", "email": "boshqa@example.com",
                "username": "uchinchi", "password": "secret1",
            },
        )
        self.assertEqual(duplicate_email.status_code, 400)

        me = self.client.get("/users/me", headers=self._auth("yangi"))
        self.assertEqual(me.json()["username"], "yangi")

    def test_login_errors(self):
        unknown = self.client.post("/users/login", data={"username": "yoq", "password": "x"})
        self.assertEqual(unknown.status_code, 400)
        wrong = self.client.post("/users/login", data={"username": "admin", "password": "x"})
        self.assertEqual(wrong.status_code, 400)
        self.assertEqual(self.client.get("/users/me").status_code, 401)
        bad_token = self.client.get("/users/me", headers={"Authorization": "Bearer abc"})
        self.assertEqual(bad_token.status_code, 401)

    def test_roles(self):
        self._create_user("rolli")
        user_headers = self._auth("rolli")
        self.assertEqual(self.client.get("/users/admin-only", headers=user_headers).status_code, 403)
        self.assertEqual(self.client.get("/users/user-or-admin", headers=user_headers).status_code, 200)

        user_id = self.client.get("/users/me", headers=user_headers).json()["id"]
        update = self.client.put(
            f"/users/update_role/{user_id}?new_role=admin", headers=self._auth(),
        )
        self.assertEqual(update.status_code, 200, update.text)
        self.assertEqual(self.client.get("/users/admin-only", headers=user_headers).status_code, 200)

        missing = self.client.put("/users/update_role/9999?new_role=admin", headers=self._auth())
        self.assertEqual(missing.status_code, 404)

    def test_upload_avatar(self):
        self._create_user("avatarli")
        headers = self._auth("avatarli")
        response = self.client.post(
            "/users/upload_avatar/",
            headers=headers,
            files={"file": ("rasm.png", b"fake-image", "image/png")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        user_id = response.json()["id"]
        self.assertEqual(response.json()["user_avatar"], f"/static/{user_id}_avatar.png")

        no_ext = self.client.post(
            "/users/upload_avatar/", headers=headers, files={"file": ("rasm", b"x")},
        )
        self.assertEqual(no_ext.status_code, 400)
