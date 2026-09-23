from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Horse, Breed, Profile


class HorseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpass123")
        self.breed = Breed.objects.create(name="Andalusian")

    def test_horse_creation(self):
        """A horse can be created with an owner and breed."""
        horse = Horse.objects.create(
            name="Starlight",
            owner=self.user,
            breed=self.breed,
            gender="F",
            conceived_date=date(2026, 1, 1),
        )
        self.assertEqual(horse.name, "Starlight")
        self.assertEqual(horse.owner, self.user)

    def test_offspring_relationship(self):
        """A horse's offspring can be found via sire/dam links."""
        sire = Horse.objects.create(name="Duke", owner=self.user, breed=self.breed, gender="M", conceived_date=date(2020, 1, 1))
        dam = Horse.objects.create(name="Rose", owner=self.user, breed=self.breed, gender="F", conceived_date=date(2020, 1, 1))
        foal = Horse.objects.create(
            name="Ember", owner=self.user, breed=self.breed, gender="F",
            sire=sire, dam=dam, conceived_date=date(2024, 1, 1),
        )

        offspring_of_sire = Horse.objects.filter(sire=sire)
        self.assertIn(foal, offspring_of_sire)

    def test_siblings_share_same_parents(self):
        """Two horses with the same sire and dam are siblings."""
        sire = Horse.objects.create(name="Duke", owner=self.user, breed=self.breed, gender="M", conceived_date=date(2020, 1, 1))
        dam = Horse.objects.create(name="Rose", owner=self.user, breed=self.breed, gender="F", conceived_date=date(2020, 1, 1))
        foal_a = Horse.objects.create(name="Ember", owner=self.user, breed=self.breed, gender="F", sire=sire, dam=dam, conceived_date=date(2024, 1, 1))
        foal_b = Horse.objects.create(name="Blaze", owner=self.user, breed=self.breed, gender="M", sire=sire, dam=dam, conceived_date=date(2024, 6, 1))

        siblings = Horse.objects.filter(sire=sire, dam=dam).exclude(id=foal_a.id)
        self.assertIn(foal_b, siblings)


class HorseListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.breed = Breed.objects.create(name="Thoroughbred")

        self.own_horse = Horse.objects.create(name="Mine", owner=self.user, breed=self.breed, gender="M", conceived_date=date(2024, 1, 1))
        self.other_horse = Horse.objects.create(name="NotMine", owner=self.other_user, breed=self.breed, gender="F", conceived_date=date(2024, 1, 1))

    def test_login_required_for_horse_list(self):
        """Logged out users are redirected away from the horse list."""
        response = self.client.get(reverse("roseline:horses"))
        self.assertNotEqual(response.status_code, 200)

    def test_horse_list_only_shows_own_horses(self):
        """A user's horse list only contains their own horses, not other users."""
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("roseline:horses"))

        self.assertContains(response, "Mine")
        self.assertNotContains(response, "NotMine")

    def test_breed_filter(self):
        """Filtering by breed only returns horses of that breed."""
        other_breed = Breed.objects.create(name="Arabian")
        Horse.objects.create(name="Sandy", owner=self.user, breed=other_breed, gender="F", conceived_date=date(2024, 1, 1))

        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("roseline:horses"), {"breed": self.breed.id})

        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Sandy")