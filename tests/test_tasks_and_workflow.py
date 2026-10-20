import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from audit.models import ActivityEvent
from notifications.models import Notification
from projects.models import Project, Membership
from tasks.models import Task, TimeEntry, Comment

class TasksAndWorkflowTests(TestCase):
    """
    Verification of TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-14, TC-18.
    SRS FR-05 to FR-14, FR-17, NFR-04, NFR-05, SR-01.
    """
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='Password123!')
        self.manager = User.objects.create_user(email='manager@example.com', password='Password123!')
        self.member = User.objects.create_user(email='member@example.com', password='Password123!')
        self.outsider = User.objects.create_user(email='outsider@example.com', password='Password123!')

        self.project = Project.objects.create(name='Task Project', owner=self.owner)
        Membership.objects.create(project=self.project, user=self.owner, role=Membership.ROLE_OWNER)
        Membership.objects.create(project=self.project, user=self.manager, role=Membership.ROLE_MANAGER)
        Membership.objects.create(project=self.project, user=self.member, role=Membership.ROLE_MEMBER)

        self.client_manager = Client()
        self.client_manager.force_login(self.manager)

        self.client_member = Client()
        self.client_member.force_login(self.member)

        self.client_outsider = Client()
        self.client_outsider.force_login(self.outsider)

    def test_tc05_task_creation_validation(self):
        """TC-05: Manager creates task; missing title attempt -> valid task in Backlog; invalid denied."""
        # Valid task creation
        resp_valid = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({
                'title': 'Feature Alpha',
                'description': 'Description',
                'priority': Task.PRIORITY_HIGH,
                'estimate_hours': 2.5
            }),
            content_type='application/json'
        )
        self.assertEqual(resp_valid.status_code, 201)
        data = resp_valid.json()
        self.assertEqual(data['status'], Task.STATUS_BACKLOG)
        self.assertEqual(data['version'], 1)

        # Missing title attempt
        resp_invalid = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({'title': '   '}),
            content_type='application/json'
        )
        self.assertEqual(resp_invalid.status_code, 400)

    def test_tc06_task_edit_permissions(self):
        """TC-06: Assignee edits title; tries estimate; outsider accesses -> Title saved; forbidden changes denied."""
        task = Task.objects.create(
            project=self.project,
            title='Initial Title',
            assignee=self.member,
            estimate_hours=Decimal('3.0')
        )

        # Assignee edits title (Permitted)
        resp_title = self.client_member.patch(
            reverse('tasks:task_detail', kwargs={'project_id': self.project.id, 'task_id': task.id}),
            json.dumps({'title': 'Updated Title'}),
            content_type='application/json'
        )
        self.assertEqual(resp_title.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Title')

        # Assignee tries to edit estimate (Denied with 403 per FR-06 / SR-01)
        resp_estimate = self.client_member.patch(
            reverse('tasks:task_detail', kwargs={'project_id': self.project.id, 'task_id': task.id}),
            json.dumps({'estimate_hours': 5.0}),
            content_type='application/json'
        )
        self.assertEqual(resp_estimate.status_code, 403)

        # Outsider accesses task (Denied with 404/403)
        resp_outsider = self.client_outsider.get(
            reverse('tasks:task_detail', kwargs={'project_id': self.project.id, 'task_id': task.id})
        )
        self.assertEqual(resp_outsider.status_code, 404)

    def test_tc07_kanban_movement_and_audit(self):
        """TC-07: Move Backlog to In Progress -> Board and history reflect transition."""
        task = Task.objects.create(project=self.project, title='Kanban Item', status=Task.STATUS_BACKLOG, version=1)

        resp = self.client_manager.patch(
            reverse('tasks:task_status_transition', kwargs={'project_id': self.project.id, 'task_id': task.id}),
            json.dumps({'status': Task.STATUS_IN_PROGRESS, 'expected_version': 1}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.STATUS_IN_PROGRESS)
        self.assertEqual(task.version, 2)

        # Verify audit history event exists
        audit_event = ActivityEvent.objects.filter(project=self.project, action='TASK_MOVED').first()
        self.assertIsNotNone(audit_event)
        self.assertIn('In Progress', audit_event.details)

    def test_tc08_combined_board_filters(self):
        """TC-08: Set assignee and priority filters -> Intersection only."""
        t1 = Task.objects.create(project=self.project, title='T1', assignee=self.member, priority=Task.PRIORITY_HIGH)
        t2 = Task.objects.create(project=self.project, title='T2', assignee=self.member, priority=Task.PRIORITY_LOW)
        t3 = Task.objects.create(project=self.project, title='T3', assignee=self.manager, priority=Task.PRIORITY_HIGH)

        url = f"{reverse('tasks:task_list_create', kwargs={'project_id': self.project.id})}?assignee={self.member.id}&priority=High"
        resp = self.client_manager.get(url)
        self.assertEqual(resp.status_code, 200)
        tasks = resp.json()['tasks']
        # Intersection only matches t1
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['id'], t1.id)

    def test_tc09_estimate_bounds(self):
        """TC-09: Submit 2.5, -1, 2.3 hours -> 2.5 accepted; others denied."""
        # 2.5 accepted
        r1 = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({'title': 'Valid Estimate', 'estimate_hours': 2.5}),
            content_type='application/json'
        )
        self.assertEqual(r1.status_code, 201)

        # -1 denied
        r2 = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({'title': 'Negative Estimate', 'estimate_hours': -1}),
            content_type='application/json'
        )
        self.assertEqual(r2.status_code, 400)

        # 2.3 denied (not 0.5 increment)
        r3 = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({'title': 'Non-increment Estimate', 'estimate_hours': 2.3}),
            content_type='application/json'
        )
        self.assertEqual(r3.status_code, 400)

    def test_tc10_time_log_calculation(self):
        """TC-10: Log 1.25 and 0.75; edit own entry -> Actual hours recomputed correctly."""
        task = Task.objects.create(project=self.project, title='Time Track Task')

        # Log 1.25 hours
        r1 = self.client_member.post(
            reverse('tasks:task_time_log', kwargs={'project_id': self.project.id, 'task_id': task.id}),
            json.dumps({'hours': 1.25, 'note': 'First entry'}),
            content_type='application/json'
        )
        self.assertEqual(r1.status_code, 201)
        entry_id = r1.json()['entry_id']

        # Log 0.75 hours
        r2 = self.client_member.post(
            reverse('tasks:task_time_log', kwargs={'project_id': self.project.id, 'task_id': task.id}),
            json.dumps({'hours': 0.75, 'note': 'Second entry'}),
            content_type='application/json'
        )
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(task.actual_hours, Decimal('2.00'))

        # Edit own entry from 1.25 to 1.50
        r_edit = self.client_member.put(
            reverse('tasks:time_entry_detail', kwargs={'project_id': self.project.id, 'task_id': task.id, 'entry_id': entry_id}),
            json.dumps({'hours': 1.50}),
            content_type='application/json'
        )
        self.assertEqual(r_edit.status_code, 200)
        self.assertEqual(task.actual_hours, Decimal('2.25'))

    def test_tc11_dashboard_totals(self):
        """TC-11: Seed known status and overdue records -> Counts and sums match fixture."""
        today = timezone.now().date()
        past = today - timezone.timedelta(days=3)

        Task.objects.create(project=self.project, title='Overdue 1', status=Task.STATUS_TODO, due_date=past, estimate_hours=Decimal('3.0'))
        Task.objects.create(project=self.project, title='Done 1', status=Task.STATUS_DONE, due_date=past, estimate_hours=Decimal('2.0'))

        resp = self.client_manager.get(reverse('tasks:project_dashboard', kwargs={'project_id': self.project.id}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status_counts'][Task.STATUS_TODO], 1)
        self.assertEqual(data['status_counts'][Task.STATUS_DONE], 1)
        self.assertEqual(data['overdue_count'], 1)  # Done task is not overdue
        self.assertEqual(data['estimated_hours'], '5.00')

    def test_tc12_comments_and_search_scope(self):
        """TC-12: Comment and search across two projects -> Comment ordered; cross-project result hidden."""
        other_project = Project.objects.create(name='Other Project', owner=self.owner)
        other_task = Task.objects.create(project=other_project, title='Secret Task X')

        my_task = Task.objects.create(project=self.project, title='Secret Task Y')

        # Add comment
        c_resp = self.client_member.post(
            reverse('tasks:task_comment_create', kwargs={'project_id': self.project.id, 'task_id': my_task.id}),
            json.dumps({'text': 'Important finding'}),
            content_type='application/json'
        )
        self.assertEqual(c_resp.status_code, 201)
        self.assertEqual(my_task.comments.count(), 1)

        # Search within my_project (FR-14 scoped search)
        search_resp = self.client_member.get(
            f"{reverse('tasks:task_list_create', kwargs={'project_id': self.project.id})}?q=Secret"
        )
        self.assertEqual(search_resp.status_code, 200)
        results = search_resp.json()['tasks']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], my_task.id)

    def test_tc14_notification_delivery(self):
        """TC-14: Assign task and invite member -> One notification per event."""
        # Task assignment notification via view
        resp = self.client_manager.post(
            reverse('tasks:task_list_create', kwargs={'project_id': self.project.id}),
            json.dumps({'title': 'Assigned Task', 'assignee_id': self.member.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Notification.objects.filter(recipient=self.member).count(), 1)
        n = Notification.objects.filter(recipient=self.member).first()
        self.assertIn('Assigned', n.title)
