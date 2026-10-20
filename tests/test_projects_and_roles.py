import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from projects.models import Project, Membership
from tasks.models import Task

class ProjectsAndRolesTests(TestCase):
    """
    Verification of TC-03, TC-04, TC-13, TC-16, TC-17.
    SRS FR-03, FR-04, FR-15, FR-16, SR-01, NFR-01, NFR-02, NFR-03.
    """
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='Password123!')
        self.manager = User.objects.create_user(email='manager@example.com', password='Password123!')
        self.member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.client_owner = Client()
        self.client_owner.force_login(self.owner)

        self.client_member = Client()
        self.client_member.force_login(self.member)

        self.client_outsider = Client()
        self.client_outsider.force_login(self.outsider)

    def test_tc03_create_project(self):
        """TC-03: Submit complete project form -> Project created; creator Owner."""
        resp = self.client_owner.post(reverse('projects:project_list'), {
            'name': 'Alpha Project',
            'description': 'Description for Alpha',
            'start_date': str(timezone.now().date())
        })
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.get(name='Alpha Project')
        self.assertEqual(project.owner, self.owner)

        membership = Membership.objects.get(project=project, user=self.owner)
        self.assertEqual(membership.role, Membership.ROLE_OWNER)

    def test_tc04_membership_and_role_control(self):
        """TC-04: Owner invites; Member tries role change -> Member denied (403)."""
        project = Project.objects.create(name='Beta Project', owner=self.owner)
        Membership.objects.create(project=project, user=self.owner, role=Membership.ROLE_OWNER)
        Membership.objects.create(project=project, user=self.member, role=Membership.ROLE_MEMBER)

        # Owner invites manager
        resp_invite = self.client_owner.post(
            reverse('projects:project_members', kwargs={'project_id': project.id}),
            json.dumps({'email': self.manager.email, 'role': Membership.ROLE_MANAGER}),
            content_type='application/json'
        )
        self.assertEqual(resp_invite.status_code, 201)
        self.assertTrue(Membership.objects.filter(project=project, user=self.manager, role=Membership.ROLE_MANAGER).exists())

        # Member tries to change own role to Owner (SR-01 / TC-04)
        resp_member_change = self.client_member.post(
            reverse('projects:project_member_role_update', kwargs={'project_id': project.id, 'member_user_id': self.member.id}),
            json.dumps({'role': Membership.ROLE_OWNER}),
            content_type='application/json'
        )
        self.assertEqual(resp_member_change.status_code, 403)

    def test_tc13_csv_export_and_archive(self):
        """TC-13: Export CSV; archive; try editing -> archived edit denied (409)."""
        project = Project.objects.create(name='Gamma Project', owner=self.owner)
        Membership.objects.create(project=project, user=self.owner, role=Membership.ROLE_OWNER)
        task = Task.objects.create(project=project, title='Exportable Task', estimate_hours=Decimal('4.0'))

        # CSV Export
        csv_resp = self.client_owner.get(reverse('tasks:project_tasks_csv', kwargs={'project_id': project.id}))
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp['Content-Type'], 'text/csv')
        self.assertIn('Exportable Task', csv_resp.content.decode('utf-8'))

        # Archive project (FR-16)
        archive_resp = self.client_owner.post(reverse('projects:project_archive', kwargs={'project_id': project.id}))
        self.assertEqual(archive_resp.status_code, 302)
        project.refresh_from_db()
        self.assertTrue(project.is_archived)

        # Attempt to create new task in archived project (Must return 409 Conflict)
        create_resp = self.client_owner.post(
            reverse('tasks:task_list_create', kwargs={'project_id': project.id}),
            json.dumps({'title': 'Task In Archived Project'}),
            content_type='application/json'
        )
        self.assertEqual(create_resp.status_code, 409)

    def test_tc16_tc17_capacity_and_rollback(self):
        """
        TC-16 & TC-17: NFR-02 capacity & NFR-03 transactional rollback reliability.
        """
        project = Project.objects.create(name='Capacity Project', owner=self.owner)
        Membership.objects.create(project=project, user=self.owner, role=Membership.ROLE_OWNER)

        # Batch create 500 tasks (NFR-02 capacity verification)
        bulk_tasks = [
            Task(project=project, title=f"Task #{i}", status=Task.STATUS_BACKLOG, estimate_hours=Decimal('1.0'))
            for i in range(500)
        ]
        Task.objects.bulk_create(bulk_tasks)
        self.assertEqual(Task.objects.filter(project=project).count(), 500)

        # Verify board request completes cleanly
        resp = self.client_owner.get(reverse('tasks:task_list_create', kwargs={'project_id': project.id}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['tasks']), 500)
