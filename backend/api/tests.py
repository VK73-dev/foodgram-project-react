from http import HTTPStatus

from django.test import Client, TestCase


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_creation(self):
        """Проверка доступности списка ингредиентов."""
        response = self.guest_client.get('/api/ingredients/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
