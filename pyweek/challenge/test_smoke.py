"""Smoke tests for challenge compatibility-critical workflows."""

from __future__ import annotations

import io
from datetime import date, timedelta
import os
import tempfile
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings

from pyweek.challenge.models import Award, Challenge, DiaryEntry, Entry, EntryAward, File


class ChallengeSmokeTests(TestCase):
    """Exercise challenge flows that are sensitive to dependency compatibility."""

    fixtures = ["challenge_smoke.json"]

    def setUp(self) -> None:
        """Set up a temporary media root and deterministic fixture passwords."""
        super().setUp()
        self._temp_media = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_media.cleanup)
        self._override = override_settings(MEDIA_ROOT=self._temp_media.name)
        self._override.enable()
        self.addCleanup(self._override.disable)

        for username in ("smoke_owner", "smoke_judge"):
            user = User.objects.get(username=username)
            user.set_password("password")
            user.save(update_fields=["password"])

    def _login(self, username: str) -> None:
        """Log in a fixture user.

        :param username: Username to authenticate.
        """
        self.assertTrue(self.client.login(username=username, password="password"))

    def _make_png_upload(self, name: str, size: tuple[int, int]) -> SimpleUploadedFile:
        """Build an in-memory PNG upload object.

        :param name: Upload filename.
        :param size: PNG dimensions as ``(width, height)``.
        :return: Django upload object.
        """
        image_data = io.BytesIO()
        image = Image.new("RGB", size, color=(255, 0, 0))
        image.save(image_data, format="PNG")
        image_data.seek(0)
        return SimpleUploadedFile(name=name, content=image_data.read(), content_type="image/png")

    def _assert_status(self, url: str, expected: int = 200) -> None:
        """Assert a GET request returns the expected status code.

        :param url: URL path to request.
        :param expected: Expected status code.
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, expected)

    def test_homepage_renders(self) -> None:
        """Homepage responds for fixture challenge data."""
        self._assert_status("/")

    def test_stats_page_renders(self) -> None:
        """Stats page renders without server errors."""
        self._assert_status("/stats/")

    def test_stats_json_renders(self) -> None:
        """Stats JSON endpoint responds with success on PostgreSQL."""
        if connection.vendor != "postgresql":
            self.skipTest("stats.json uses PostgreSQL-specific SQL")
        self._assert_status("/stats.json")

    def test_all_games_page_renders(self) -> None:
        """All-games page renders."""
        self._assert_status("/all_games/")

    def test_challenges_page_renders(self) -> None:
        """Previous challenge list page renders."""
        self._assert_status("/challenges/")

    def test_challenge_display_renders(self) -> None:
        """Challenge detail page renders."""
        self._assert_status("/99/")

    def test_challenge_entries_page_renders(self) -> None:
        """Challenge entries page renders."""
        self._assert_status("/99/entries/")

    def test_challenge_diaries_page_renders(self) -> None:
        """Challenge diary list page renders."""
        self._assert_status("/99/diaries/")

    def test_challenge_ratings_page_renders(self) -> None:
        """Challenge ratings page renders."""
        self._assert_status("/99/ratings/", expected=302)

    def test_challenge_downloads_json_renders(self) -> None:
        """Challenge downloads API responds."""
        self._assert_status("/99/downloads.json")

    def test_entry_page_renders(self) -> None:
        """Entry detail page renders."""
        self._assert_status("/e/smoke-entry/")

    def test_entry_ratings_page_renders(self) -> None:
        """Entry ratings page renders."""
        self._assert_status("/e/smoke-entry/ratings/", expected=302)

    def test_messages_page_renders(self) -> None:
        """Message list page renders."""
        self._assert_status("/messages/")

    def test_diary_feed_renders(self) -> None:
        """Diary RSS feed renders."""
        self._assert_status("/d/feed/")

    def test_profile_rejects_wrong_old_password(self) -> None:
        self._login("smoke_owner")
        response = self.client.post("/profile/", {
            "passwd-old_password": "wrong-password",
            "passwd-password": "Boats-and-dragons-42!",
            "passwd-again": "Boats-and-dragons-42!",
        })
        self.assertContains(response, "This password is not correct.")
        self.assertEqual(
            response.context["password_form"].errors["old_password"],
            ["This password is not correct."],
        )
        self.assertTrue(User.objects.get(username="smoke_owner").check_password("password"))

    def test_profile_rejects_incomplete_or_invalid_password_changes(self) -> None:
        self._login("smoke_owner")
        for old, new, again, error in (
            ("", "Boats-and-dragons-42!", "Boats-and-dragons-42!", "You must enter the old password."),
            ("password", "", "", "You must enter the new password."),
            ("password", "Boats-and-dragons-42!", "different", "Supplied passwords did not match."),
            ("password", "123", "123", "This password is too short."),
            ("wrong-password", "", "", "This password is not correct."),
        ):
            with self.subTest(error=error):
                response = self.client.post("/profile/", {
                    "passwd-old_password": old,
                    "passwd-password": new,
                    "passwd-again": again,
                })
                self.assertContains(response, error)
                self.assertTrue(User.objects.get(username="smoke_owner").check_password("password"))

    def test_profile_password_change_keeps_user_logged_in(self) -> None:
        self._login("smoke_owner")
        new_password = "Boats-and-dragons-42!"
        response = self.client.post("/profile/", {
            "passwd-old_password": "password",
            "passwd-password": new_password,
            "passwd-again": new_password,
        })
        self.assertRedirects(response, "/profile/")
        user = User.objects.get(username="smoke_owner")
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password("password"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_profile_update_without_password_change(self) -> None:
        self._login("smoke_owner")
        response = self.client.post("/profile/", {"profile-email_replies": "on"})
        self.assertRedirects(response, "/profile/")
        self.assertTrue(User.objects.get(username="smoke_owner").check_password("password"))

    def test_profile_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from profile page."""
        self._assert_status("/profile/", expected=302)

    def test_entry_manage_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from entry manage page."""
        self._assert_status("/e/smoke-entry/manage/", expected=302)

    def test_entry_members_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from entry members page."""
        self._assert_status("/e/smoke-entry/members/", expected=302)

    def test_entry_upload_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from upload page."""
        self._assert_status("/e/smoke-entry/upload/", expected=302)

    def test_upload_award_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from upload-award page."""
        self._assert_status("/e/smoke-entry/upload_award/", expected=302)

    def test_give_award_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from give-award page."""
        self._assert_status("/e/smoke-entry/give_award/", expected=302)

    def test_message_add_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from thread creation page."""
        self._assert_status("/message_add/", expected=302)

    def test_entry_diary_redirects_when_anonymous(self) -> None:
        """Anonymous users are redirected from entry diary creation page."""
        self._assert_status("/e/smoke-entry/diary/", expected=302)

    def test_rating_dashboard_forbidden_when_anonymous(self) -> None:
        """Rating dashboard rejects anonymous users."""
        self._assert_status("/99/rating-dashboard", expected=403)

    def test_owner_can_view_entry_upload_page(self) -> None:
        """Entry members can open the upload form."""
        self._login("smoke_owner")
        self._assert_status("/e/smoke-entry/upload/")

    def test_owner_can_upload_regular_file(self) -> None:
        """Entry members can upload regular files."""
        self._login("smoke_owner")
        response = self.client.post(
            "/e/smoke-entry/upload/",
            {
                "content": SimpleUploadedFile("build.zip", b"zip-data", content_type="application/zip"),
                "description": "Initial build",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(File.objects.filter(entry_id="smoke-entry", description="Initial build").exists())

    def test_owner_can_upload_screenshot_and_thumbnail(self) -> None:
        """Screenshot uploads create thumbnail metadata and image files."""
        self._login("smoke_owner")
        response = self.client.post(
            "/e/smoke-entry/upload/",
            {
                "content": self._make_png_upload("screenshot.png", (800, 600)),
                "description": "Gameplay screenshot",
                "is_screenshot": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        uploaded_file = File.objects.get(entry_id="smoke-entry", description="Gameplay screenshot")
        self.assertTrue(uploaded_file.is_screenshot)
        self.assertGreater(uploaded_file.thumb_width, 0)
        thumb_path = os.path.join(self._temp_media.name, f"{uploaded_file.content.name}-thumb.png")
        self.assertTrue(os.path.exists(thumb_path))

    def test_owner_upload_persists_expected_filename(self) -> None:
        """Uploaded files keep expected challenge/entry path prefixes."""
        self._login("smoke_owner")
        self.client.post(
            "/e/smoke-entry/upload/",
            {
                "content": SimpleUploadedFile("named.zip", b"aaa", content_type="application/zip"),
                "description": "Path check",
            },
        )
        uploaded_file = File.objects.get(entry_id="smoke-entry", description="Path check")
        self.assertTrue(uploaded_file.content.name.startswith("99/smoke-entry/"))

    def test_owner_can_delete_uploaded_file(self) -> None:
        """Entry members can delete previously uploaded files."""
        self._login("smoke_owner")
        self.client.post(
            "/e/smoke-entry/upload/",
            {
                "content": SimpleUploadedFile("todelete.zip", b"zip-data", content_type="application/zip"),
                "description": "Delete me",
            },
        )
        uploaded_file = File.objects.get(entry_id="smoke-entry", description="Delete me")
        response = self.client.post(f"/e/smoke-entry/delete/{uploaded_file.content.name}", {"confirm": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(File.objects.filter(pk=uploaded_file.pk).exists())

    def test_owner_can_create_site_thread(self) -> None:
        """Authenticated users can create a global discussion thread."""
        self._login("smoke_owner")
        response = self.client.post(
            "/message_add/",
            {
                "title": "Smoke thread",
                "content": "<p>Hello smoke test</p>",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DiaryEntry.objects.filter(title="Smoke thread", entry__isnull=True).exists())

    def test_owner_can_create_entry_diary(self) -> None:
        """Entry members can create entry diary posts."""
        self._login("smoke_owner")
        response = self.client.post(
            "/e/smoke-entry/diary/",
            {
                "title": "Diary smoke",
                "content": "<p>Build update</p>",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DiaryEntry.objects.filter(title="Diary smoke", entry_id="smoke-entry").exists())

    def test_judge_can_upload_award_and_assign(self) -> None:
        """Non-team users can upload and assign awards to an entry."""
        self._login("smoke_judge")
        response = self.client.post(
            "/e/smoke-entry/upload_award/",
            {
                "content": self._make_png_upload("award.png", (64, 64)),
                "description": "Best atmosphere",
            },
        )
        self.assertEqual(response.status_code, 302)
        award = Award.objects.get(creator__username="smoke_judge", description="Best atmosphere")
        self.assertTrue(EntryAward.objects.filter(award=award, entry_id="smoke-entry", challenge_id=99).exists())

    def test_judge_can_give_existing_award(self) -> None:
        """Users can give an already-owned award to an entry."""
        self._login("smoke_judge")
        award = Award.objects.create(
            creator=User.objects.get(username="smoke_judge"),
            content=self._make_png_upload("existing-award.png", (64, 64)),
            description="Gameplay polish",
        )
        response = self.client.post("/e/smoke-entry/give_award/", {"award": str(award.pk)})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EntryAward.objects.filter(award=award, entry_id="smoke-entry").exists())

    def test_judge_duplicate_award_assignment_blocked(self) -> None:
        """Duplicate entry-award assignments are prevented."""
        self._login("smoke_judge")
        award = Award.objects.create(
            creator=User.objects.get(username="smoke_judge"),
            content=self._make_png_upload("unique-award.png", (64, 64)),
            description="Sound design",
        )
        self.client.post("/e/smoke-entry/give_award/", {"award": str(award.pk)})
        response = self.client.post("/e/smoke-entry/give_award/", {"award": str(award.pk)})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(EntryAward.objects.filter(award=award, entry_id="smoke-entry").count(), 1)

    def test_owner_cannot_award_own_entry(self) -> None:
        """Team members cannot give awards to their own entry."""
        self._login("smoke_owner")
        response = self.client.get("/e/smoke-entry/upload_award/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Award.objects.filter(creator__username="smoke_owner").count(), 0)

    def test_register_page_available_with_open_challenge(self) -> None:
        """Register page is available while challenge registration is open."""
        self._assert_status("/register/")


class EntryTitleTests(TestCase):
    """Team names must be unique within a challenge, including on edits."""

    fixtures = ["challenge_smoke.json"]

    def setUp(self):
        self.user = User.objects.get(username="smoke_owner")
        self.client.force_login(self.user)
        self.challenge = Challenge.objects.get(pk=99)
        self.challenge.end = date.today() + timedelta(days=7)
        self.challenge.save()
        self.entry = Entry.objects.get(pk="smoke-entry")
        self.data = {
            "name": "new-entry",
            "title": self.entry.title,
            "users": self.user.username,
            "game": "Test Game",
        }

    def test_add_duplicate_title_shows_field_error(self):
        self.entry.title = "같은 팀 이름"
        self.entry.save()
        self.data["title"] = "  같은 팀 이름  "
        response = self.client.post("/99/entry_add/", self.data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A team with this name already exists in this challenge.")
        self.assertIn("title", response.context["form"].errors)
        self.assertFalse(Entry.objects.filter(pk="new-entry").exists())

    def test_add_title_used_in_another_challenge(self):
        other = Challenge.objects.create(
            number=100, title="Other challenge",
            start=date.today(), end=date.today() + timedelta(days=7),
            is_rego_open=True,
        )
        response = self.client.post(f"/{other.pk}/entry_add/", self.data)
        self.assertRedirects(response, "/e/new-entry/", fetch_redirect_response=False)
        entry = Entry.objects.get(pk="new-entry")
        self.assertEqual(entry.challenge, other)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(list(entry.users.all()), [self.user])

    def test_manage_duplicate_title_shows_field_error(self):
        Entry.objects.create(
            name="other-entry", title="Other team",
            challenge=self.challenge, user=self.user,
        )
        self.data["title"] = "Other team"
        response = self.client.post("/e/smoke-entry/manage/", self.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Smoke Team")

    def test_manage_unchanged_title(self):
        response = self.client.post("/e/smoke-entry/manage/", self.data)
        self.assertRedirects(response, "/e/smoke-entry/", fetch_redirect_response=False)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.game, "Test Game")

    def test_add_unique_title(self):
        self.data["title"] = "New team"
        response = self.client.post("/99/entry_add/", self.data)
        self.assertRedirects(response, "/e/new-entry/", fetch_redirect_response=False)
        self.assertEqual(Entry.objects.get(pk="new-entry").title, "New team")
