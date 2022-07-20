from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from shopping_list.models import ShoppingList, ShoppingItem

User = get_user_model()


@pytest.mark.django_db
def test_valid_shopping_list_is_created(create_user, create_authenticated_client):
    url = reverse("all_shopping_lists")
    data = {
        "name": "Groceries",
    }
    client = create_authenticated_client(create_user())
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert ShoppingList.objects.get().name == "Groceries"


@pytest.mark.django_db
def test_shopping_list_name_missing_returns_bad_request(create_user, create_authenticated_client):
    client = create_authenticated_client(create_user())
    data = {
        "something_else": "blahblah",
    }

    url = reverse("all_shopping_lists")
    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_client_retrieves_only_shopping_lists_they_are_member_of(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = ShoppingList.objects.create(name="Books")
    shopping_list.members.add(user)

    another_user = User.objects.create_user("another", "another@example.com", "supersecretpassword")
    create_shopping_list(another_user)

    url = reverse("all_shopping_lists")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Books"


@pytest.mark.django_db
def test_shopping_list_is_retrieved_by_id(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.get(url, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Groceries"


@pytest.mark.django_db
def test_shopping_list_includes_only_corresponding_items(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    another_shopping_list = create_shopping_list(user)
    ShoppingItem.objects.create(shopping_list=shopping_list, name="Eggs", purchased=False)
    ShoppingItem.objects.create(shopping_list=another_shopping_list, name="The Seven Sisters", purchased=False)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.get(url)

    assert len(response.data["unpurchased_items"]) == 1
    assert response.data["unpurchased_items"][0]["name"] == "Eggs"


@pytest.mark.django_db
def test_shopping_list_name_is_changed(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "name": "Food",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.put(url, data=data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Food"


@pytest.mark.django_db
def test_shopping_list_not_changed_because_name_missing(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "something_else": "blahblah",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.put(url, data=data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_shopping_list_name_is_changed_with_partial_update(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "name": "Food",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.patch(url, data=data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Food"


@pytest.mark.django_db
def test_partial_update_with_missing_name_has_no_impact(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "something_else": "blahblah",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.patch(url, data=data, format="json")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_shopping_list_is_deleted(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(ShoppingList.objects.all()) == 0


@pytest.mark.django_db
def test_valid_shopping_item_is_created(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "name": "Milk",
        "purchased": False,
    }

    url = reverse("list_add_shopping_item", args=[shopping_list.id])
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_shopping_item_missing_data_returns_bad_request(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)
    data = {
        "name": "Milk",
    }

    url = reverse("list_add_shopping_item", args=[shopping_list.id])
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_shopping_item_is_retrieved_by_id(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name="Chocolate", user=user)

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Chocolate"


@pytest.mark.django_db
def test_change_shopping_item_purchased_status(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name="Chocolate", user=user)
    data = {
        "name": "Chocolate",
        "purchased": True,
    }

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert ShoppingItem.objects.get().purchased is True


@pytest.mark.django_db
def test_change_shopping_item_purchased_status_with_missing_data_returns_bad_request(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name="Chocolate", user=user)
    data = {
        "purchased": True,
    }

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_change_shopping_item_purchased_status_with_partial_update(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name="Chocolate", user=user)
    data = {
        "purchased": True,
    }

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert ShoppingItem.objects.get().purchased is True


@pytest.mark.django_db
def test_shopping_item_is_deleted(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_item = create_shopping_item(name="Chocolate", user=user)

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(ShoppingItem.objects.all()) == 0


@pytest.mark.django_db
def test_update_shopping_list_restricted_if_not_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(shopping_list_creator)
    data = {
        "name": "Food",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.put(url, data=data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_partial_update_shopping_list_restricted_if_not_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(shopping_list_creator)
    data = {
        "name": "Food",
    }

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.patch(url, data=data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_shopping_list_restricted_if_not_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(shopping_list_creator)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.delete(url, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_retrieve_shopping_list(create_user, create_shopping_list, admin_client):
    user = create_user()
    shopping_list = create_shopping_list(user)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = admin_client.get(url, format="json")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_not_member_of_list_cannot_add_shopping_item(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    shopping_list = create_shopping_list(shopping_list_creator)
    data = {
        "name": "Milk",
        "purchased": False,
    }

    url = reverse("list_add_shopping_item", args=[shopping_list.id])
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_add_shopping_items(create_user, create_shopping_list, admin_client):
    user = create_user()
    shopping_list = create_shopping_list(user)
    data = {
        "name": "Milk",
        "purchased": False,
    }

    url = reverse("list_add_shopping_item", kwargs={"pk": shopping_list.id})
    response = admin_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_shopping_item_detail_access_restricted_if_not_member_of_shopping_list(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    shopping_item = create_shopping_item(name="Chocolate", user=shopping_list_creator)

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.get(url, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_shopping_item_partial_update_restricted_if_not_member_of_shopping_list(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    shopping_item = create_shopping_item(name="Chocolate", user=shopping_list_creator)
    data = {
        "purchased": True,
    }

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.patch(url, data=data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_shopping_item_delete_restricted_if_not_member_of_shopping_list(create_user, create_authenticated_client, create_shopping_item):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    shopping_item = create_shopping_item(name="Chocolate", user=shopping_list_creator)

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = client.delete(url, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_retrieve_single_shopping_item(create_user, create_shopping_item, admin_client):
    user = create_user()
    shopping_item = create_shopping_item(name="Milk", user=user)

    url = reverse("shopping_item_detail", kwargs={"pk": shopping_item.shopping_list.id, "item_pk": shopping_item.id})
    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_list_shopping_items_is_retrieved_by_shopping_list_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)
    shopping_item_1 = ShoppingItem.objects.create(name="Oranges", purchased=False, shopping_list=shopping_list)
    shopping_item_2 = ShoppingItem.objects.create(name="Milk", purchased=False, shopping_list=shopping_list)

    client = create_authenticated_client(user)
    url = reverse("list_add_shopping_item", kwargs={"pk": shopping_list.id})
    response = client.get(url)

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["name"] == shopping_item_1.name
    assert response.data["results"][1]["name"] == shopping_item_2.name


@pytest.mark.django_db
def test_not_member_can_not_retrieve_shopping_items(create_user, create_authenticated_client, create_shopping_item):
    shopping_list_creator = User.objects.create_user("creator", "creator@example.com", "supersecretpassword")
    shopping_item = create_shopping_item(name="Milk", user=shopping_list_creator)

    user = create_user()
    client = create_authenticated_client(user)
    url = reverse("list_add_shopping_item", args=[shopping_item.shopping_list.id])
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_shopping_items_only_the_ones_belonging_to_the_same_shopping_list(create_user, create_authenticated_client, create_shopping_list, create_shopping_item):
    user = create_user()

    shopping_list = ShoppingList.objects.create(name="My shopping list")
    shopping_list.members.add(user)
    shopping_item_from_this_list = ShoppingItem.objects.create(name="Oranges", purchased=False, shopping_list=shopping_list)

    another_shopping_list = ShoppingList.objects.create(name="Another shopping list")
    another_shopping_list.members.add(user)
    ShoppingItem.objects.create(name="Item from another list", purchased=False, shopping_list=another_shopping_list)

    client = create_authenticated_client(user)
    url = reverse("list_add_shopping_item", args=[shopping_list.id])
    response = client.get(url)

    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == shopping_item_from_this_list.name


@pytest.mark.django_db
def test_max_3_shopping_items_on_shopping_list(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)

    ShoppingItem.objects.create(name="Eggs", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Chocolate", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Milk", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Mango", purchased=False, shopping_list=shopping_list)

    url = reverse("shopping_list_detail", args=[shopping_list.id])
    client = create_authenticated_client(user)
    response = client.get(url, format="json")

    assert len(response.data["unpurchased_items"]) == 3


@pytest.mark.django_db
def test_all_shopping_items_on_shopping_list_unpurchased(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)

    ShoppingItem.objects.create(name="Eggs", purchased=False, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Chocolate", purchased=True, shopping_list=shopping_list)
    ShoppingItem.objects.create(name="Milk", purchased=False, shopping_list=shopping_list)

    client = create_authenticated_client(user)
    url = reverse("shopping_list_detail", args=[shopping_list.id])
    response = client.get(url, format="json")

    assert len(response.data["unpurchased_items"]) == 2


@pytest.mark.django_db
def test_duplicate_item_on_list_bad_request(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)
    ShoppingItem.objects.create(name="Milk", purchased=False, shopping_list=shopping_list)

    client = create_authenticated_client(user)
    url = reverse("list_add_shopping_item", args=[shopping_list.id])
    data = {
        "name": "Milk",
        "purchased": False,
    }
    response = client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert len(shopping_list.shopping_items.all()) == 1


@pytest.mark.django_db
def test_correct_order_shopping_lists(create_user, create_authenticated_client):
    user = create_user()
    old_time = timezone.now() - timedelta(days=1)
    older_time = timezone.now() - timedelta(days=100)

    with mock.patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = old_time
        ShoppingList.objects.create(name="Old").members.add(user)

        mock_now.return_value = older_time
        ShoppingList.objects.create(name="Oldest").members.add(user)

    ShoppingList.objects.create(name="New").members.add(user)

    client = create_authenticated_client(user)
    url = reverse("all_shopping_lists")
    response = client.get(url)

    assert response.data["results"][0]["name"] == "New"
    assert response.data["results"][1]["name"] == "Old"
    assert response.data["results"][2]["name"] == "Oldest"


@pytest.mark.django_db
def test_shopping_list_order_changed_when_item_marked_purchased(create_user, create_authenticated_client):
    user = create_user()
    more_recent_time = timezone.now() - timedelta(days=1)
    older_time = timezone.now() - timedelta(days=20)

    with mock.patch("django.utils.timezone.now") as mock_now:
        mock_now.return_value = older_time
        older_list = ShoppingList.objects.create(name="Older")
        older_list.members.add(user)
        shopping_item_on_older_list = ShoppingItem.objects.create(name="Milk", purchased=False, shopping_list=older_list)

        mock_now.return_value = more_recent_time
        ShoppingList.objects.create(name="Recent", last_interaction=timezone.now() - timedelta(days=100)).members.add(user)

    shopping_item_url = reverse("shopping_item_detail", kwargs={"pk": older_list.id, "item_pk": shopping_item_on_older_list.id})
    shopping_lists_url = reverse("all_shopping_lists")
    data = {
        "purchased": True,
    }

    client = create_authenticated_client(user)
    client.patch(shopping_item_url, data)
    response = client.get(shopping_lists_url)

    assert response.data["results"][0]["name"] == "Older"
    assert response.data["results"][1]["name"] == "Recent"


@pytest.mark.django_db
def test_call_with_token_authentication():
    username = "test"
    password = "supersecret"
    User.objects.create_user(username, password=password)

    client = APIClient()
    token_url = reverse("api_token_auth")
    data = {
        "username": username,
        "password": password,
    }

    token_response = client.post(token_url, data, format="json")
    token = token_response.data["token"]

    url = reverse("all_shopping_lists")
    client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_add_members_list_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)

    another_member = User.objects.create_user(username="another", password="whocares")
    third_member = User.objects.create_user(username="third_wheel", password="doesntmatter")

    data = {
        "members": [another_member.id, third_member.id],
    }

    client = create_authenticated_client(user)
    url = reverse("shopping_list_add_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert len(response.data["members"]) == 3
    assert another_member.id in response.data["members"]
    assert third_member.id in response.data["members"]


@pytest.mark.django_db
def test_add_members_not_list_members(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)

    list_creator = User.objects.create(username="creator", password="doesn'tmatter")
    shopping_list = create_shopping_list(list_creator)

    data = {
        "members": [user.id],
    }

    url = reverse("shopping_list_add_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_add_members_wrong_data(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    data = {
        "members": [11, 13],
    }

    url = reverse("shopping_list_add_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_remove_members_list_member(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    shopping_list = create_shopping_list(user)

    another_member = User.objects.create_user(username="another", password="whocares")
    third_member = User.objects.create_user(username="third_wheel", password="doesntmatter")

    shopping_list.members.add(another_member)
    shopping_list.members.add(third_member)

    data = {
        "members": [another_member.id, third_member.id],
    }

    client = create_authenticated_client(user)
    url = reverse("shopping_list_remove_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert len(response.data["members"]) == 1
    assert another_member.id not in response.data["members"]
    assert third_member.id not in response.data["members"]


@pytest.mark.django_db
def test_remove_members_not_list_members(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)

    list_creator = User.objects.create(username="creator", password="doesn'tmatter")
    shopping_list = create_shopping_list(list_creator)

    data = {
        "members": [user.id],
    }

    url = reverse("shopping_list_remove_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_remove_members_wrong_data(create_user, create_authenticated_client, create_shopping_list):
    user = create_user()
    client = create_authenticated_client(user)
    shopping_list = create_shopping_list(user)

    data = {
        "members": [11, 13],
    }

    url = reverse("shopping_list_remove_members", args=[shopping_list.id])
    response = client.put(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
