from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from apps.accounts.models import User
from apps.sponsors.models import Sponsor
from apps.assignments.models import Assignment
from apps.content.models import ContentEntry
from apps.contentlist.models import ContentListItem
from apps.audio.models import AudioItem
from apps.scripts.models import Script
from apps.finalpackage.models import FinalPackage
from apps.notices.models import Notice
from apps.notifications.models import Notification

CAPTIONS = [
    "Barishal: Youth dies of electrocution",
    "Chapainawabganj: bumper mango harvest",
    "Sylhet: flood situation worsens",
    "Cox's Bazar: tourist rush surges",
    "Rajshahi: football tournament inaugurated",
    "Dhaka: new metro route launched",
    "Khulna: factory fire breaks out",
    "Dinajpur: agriculture fair held",
    "Satkhira: embankment construction starts",
    "Comilla: historic mosque restoration",
]

HEADLINES = [
    "Barishal: Electrical short circuit fire, 1 dead",
    "Chapainawabganj: Mango yield exceeds target",
    "Sylhet: Heavy rain floods low-lying areas",
    "Cox's Bazar: Eid holiday sees lakhs of tourists",
    "Rajshahi: Friendly football tournament begins",
    "Dhaka: Metro Route-6 inaugurated today",
    "Khulna: Massive fire at garment factory",
    "Dinajpur: Three-day agriculture fair starts",
    "Satkhira: Coastal embankment construction begins",
    "Comilla: Historic mosque restoration completed",
]

SLUGS = [
    "barishal-electrocution-death",
    "chapainawabganj-mango-harvest",
    "sylhet-flood-situation",
    "cox-bazar-tourist-crowd",
    "rajshahi-football-tournament",
    "dhaka-metro-route-launch",
    "khulna-factory-fire",
    "dinajpur-agriculture-fair",
    "satkhira-embankment-construction",
    "comilla-historic-mosque-restoration",
]

DISTRICTS = [
    "Barishal", "Chapainawabganj", "Sylhet", "Coxs Bazar",
    "Rajshahi", "Dhaka", "Khulna", "Dinajpur", "Satkhira", "Comilla",
]

REPORTERS = [
    "Rafiqul Islam", "Sabina Yasmin", "Zahid Hasan", "Suman Chandra Das",
    "Nasrin Akter", "Helal Uddin", "Sharmi Rani De", "Abdur Rahim",
    "Fatema Begum", "Idris Ali",
]

BODIES = [
    "Barishal city's Kazipara area: a youth died of electrocution. Local sources say the incident occurred during electrical repair work due to a short circuit. The deceased was identified as Md. Jamal Hossain (28). Family alleges longstanding faulty electrical connections were never fixed.",
    "Chapainawabganj district has seen a bumper mango harvest this year. Agriculture department sources say production exceeded targets by 20 percent. The highest collections were recorded in Gomastapur and Shibganj upazilas. Traders say farmers are getting fair prices.",
    "Sylhet: Three days of continuous heavy rain has submerged low-lying areas. Several unions in Sunamganj and Moulvibazar districts face flood conditions. The district administration says it is prepared. Navy and fire service rescue teams are on standby.",
    "Cox's Bazar beach: Lakhs of tourists have arrived for the Eid holiday. Hotels and motels report 100 percent occupancy. Tourism authorities have deployed special security measures including lifeguards and water police.",
    "Rajshahi: A friendly football tournament was inaugurated at Saheb Bazar Gymnasium ground. Sixteen teams from the district are participating. The DC was chief guest. The final will be held Friday with cash prizes and trophies.",
    "Dhaka Mass Transit Company Limited's new Metro Route-6 was inaugurated today. The route from Motijheel to Uttara North is expected to significantly reduce traffic congestion. The Road Transport Minister attended. It opens to the public tomorrow.",
    "Khulna: A massive fire broke out at a garment factory in Phultala. Twelve fire service units are working to control it. No casualties reported initially. Factory authorities suspect electrical fault. Damage assessment is underway.",
    "Dinajpur: The District Agricultural Extension Department has organized a three-day agriculture fair. Modern farming technology, improved seeds and fertilizers are on display. Free training workshops for farmers are also being held. Thousands attended on day one.",
    "Satkhira: Construction of a 15-km embankment to prevent flooding in coastal areas has begun. The Water Development Board is implementing the project funded by the Ministry of Water Resources. It will protect 10,000 hectares of land. Completion is expected this year.",
    "Comilla: Restoration work of the historic Shalman Shah Mosque has been completed. Built during the Mughal era, the mosque is over 200 years old. The Department of Archaeology supervised the work. The original structure was preserved. Prayers have resumed.",
]

NOTICES = [
    ("Office closed for Eid", "Office will remain closed from 25 July to 28 July for Eid holidays. Everyone is requested to complete content uploads in advance."),
    ("New sponsor added", "Pran-RFL Group has been added as a new sponsor. Please select sponsor when entering content."),
    ("Script submission guidelines", "Please format headlines and body properly when submitting scripts. Avoid spelling and grammatical errors."),
    ("Training workshop", "A training workshop will be held on 15 August. Everyone is requested to attend. Time: 10 AM to 4 PM."),
    ("Final package upload process", "Ensure correct format and file size when uploading final packages. Set status to Complete after full upload."),
]


class Command(BaseCommand):
    help = 'Seed 10 sets of realistic dummy data for all core models'

    def handle(self, *args, **options):
        if User.objects.exclude(username='admin').count() >= 9:
            self.stdout.write(self.style.WARNING(
                'Seed data already exists (9+ non-admin users found). Skipping.'
            ))
            return

        today = date.today()

        # ─── ADMIN USER ───
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults=dict(
                full_name='System Admin',
                office_id='ADM-001',
                designation='Chief Administrator',
                phone='01700000000',
                blood_group='O+',
                is_admin=True,
                is_founder=True,
                is_staff=True,
                is_superuser=True,
                password=make_password('admin123'),
            ),
        )
        self.stdout.write(f'  [OK] Admin user: {admin.username}')

        # ─── 10 REGULAR USERS ───
        users = [admin]
        for i in range(10):
            u, created = User.objects.get_or_create(
                username=f'reporter{i+1:02d}',
                defaults=dict(
                    full_name=REPORTERS[i],
                    office_id=f'RPT-{i+1:03d}',
                    designation='Correspondent',
                    phone=f'017{i+1:08d}',
                    blood_group=['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-', 'A+', 'B+'][i],
                    is_active=True,
                    password=make_password('reporter123'),
                ),
            )
            users.append(u)
            self.stdout.write(f'  [OK] User {i+1}/10: {u.username}')

        # ─── 10 SPONSORS ───
        sponsor_data = [
            ('Grameenphone', 8, 240, 'tvc+gpi+popup'),
            ('Banglalink', 6, 180, 'doggy+tvc'),
            ('Robi', 6, 180, 'tvc+popup'),
            ('Pran-RFL Group', 4, 120, 'tvc+gpi'),
            ('SQF', 4, 120, 'popup+doggy'),
            ('Akij Group', 3, 90, 'tvc'),
            ('Beximco', 3, 90, 'popup'),
            ('Unilever', 5, 150, 'tvc+popup+gpi'),
            ('Nestle', 4, 120, 'tvc+doggy'),
            ('Marico', 3, 90, 'popup+gpi'),
        ]
        sponsors = []
        for i, (name, daily, total, ctype) in enumerate(sponsor_data):
            s, created = Sponsor.objects.get_or_create(
                name=name,
                defaults=dict(
                    daily_quota=daily, total_quota=total,
                    start_date=today - timedelta(days=30),
                    end_date=today + timedelta(days=60),
                    content_type=ctype,
                    has_doggy='doggy' in ctype,
                    has_popup='popup' in ctype,
                    has_tvc='tvc' in ctype,
                    has_gpi='gpi' in ctype,
                ),
            )
            sponsors.append(s)
            label = '[NEW]' if created else '[SKIP]'
            self.stdout.write(f'  {label} Sponsor {i+1}/10: {name}')

        # ─── 10 SETS: assignment + linked records ───
        for i in range(10):
            assign_date = today - timedelta(days=9 - i)
            reporter_user = users[i + 1]
            creator = users[(i + 3) % 10 + 1]
            statuses = ['Assigned', 'Processing', 'Done', 'Done', 'Done',
                        'Processing', 'Assigned', 'Done', 'Processing', 'Assigned']
            status = statuses[i]

            assignment, created = Assignment.objects.get_or_create(
                caption=CAPTIONS[i],
                assign_date=assign_date,
                defaults=dict(
                    source_link=f'https://fb.watch/seed{i+1:03d}',
                    district=DISTRICTS[i],
                    reporter=REPORTERS[i],
                    reporter_user=reporter_user,
                    status=status,
                    member=creator,
                    created_by=creator,
                ),
            )
            if created:
                assignment.updated_by = creator
                assignment.save(update_fields=['updated_by'])
            self.stdout.write(f'  [{"NEW" if created else "SKIP"}] Set {i+1}/10: {assignment.caption[:50]}')

            entry_date = assign_date

            # ContentEntry
            ContentEntry.objects.get_or_create(
                slug=SLUGS[i],
                entry_date=entry_date,
                defaults=dict(
                    entry_time=timezone.now().time(),
                    headline=HEADLINES[i],
                    member=reporter_user,
                    links={
                        'youtube': f'https://youtube.com/watch?v=vid{i+1:03d}',
                        'facebook': f'https://facebook.com/watch?v=fbreel{i+1:03d}',
                    },
                    sponsor=sponsors[i] if i % 2 == 0 else None,
                    assignment=assignment,
                    comment=f'Editor note: Video editing required #{i+1}',
                    created_by=reporter_user,
                ),
            )

            # ContentListItem
            ContentListItem.objects.get_or_create(
                list_date=entry_date,
                content=HEADLINES[i],
                defaults=dict(
                    source=['district', 'reuters', 'social', 'studio'][i % 4],
                    district=DISTRICTS[i],
                    footage_source=['FTP', 'WhatsApp', 'Gmail', 'Google Drive', 'Ingest'][i % 5],
                    member=reporter_user,
                    assignment=assignment,
                    created_by=reporter_user,
                ),
            )

            # AudioItem
            AudioItem.objects.get_or_create(
                audio_date=entry_date,
                title=HEADLINES[i],
                defaults=dict(
                    source=['district', 'reuters', 'social', 'studio'][(i + 1) % 4],
                    district=DISTRICTS[i],
                    duration=f'{2 + i}:{15 + i * 3:02d}',
                    file_link=f'https://cdn.example.com/audio/{SLUGS[i]}.mp3',
                    voice_over=['', 'Rafiq', 'Sabina', 'Zahid'][i % 4],
                    member=reporter_user,
                    assignment=assignment,
                    created_by=reporter_user,
                ),
            )

            # Script
            Script.objects.get_or_create(
                script_date=entry_date,
                headline=HEADLINES[i],
                defaults=dict(
                    source=['district', 'reuters', 'social', 'studio'][(i + 2) % 4],
                    writer=reporter_user,
                    district=DISTRICTS[i],
                    district_reporter=REPORTERS[i],
                    body=BODIES[i],
                    assignment=assignment,
                    status=['draft', 'pending', 'approved'][i % 3],
                    approved_by=admin if i % 3 == 2 else None,
                    approved_at=timezone.now() if i % 3 == 2 else None,
                    created_by=reporter_user,
                ),
            )

            # FinalPackage
            FinalPackage.objects.get_or_create(
                package_date=entry_date,
                title=HEADLINES[i],
                defaults=dict(
                    producer=REPORTERS[(i + 1) % 10],
                    editor=REPORTERS[(i + 2) % 10],
                    runtime=f'{3 + i % 5}:{30 + i * 5:02d}',
                    file_link=f'https://cdn.example.com/final/{SLUGS[i]}.mp4',
                    notes=f'Editor: News desk final check done',
                    status=['draft', 'complete', 'approved'][i % 3],
                    member=reporter_user,
                    assignment=assignment,
                    created_by=reporter_user,
                ),
            )

            # Notification
            Notification.objects.get_or_create(
                title=CAPTIONS[i],
                recipient=reporter_user,
                notification_type='assignment',
                defaults=dict(
                    message=f'New assignment for you: {CAPTIONS[i]}',
                    link=f'/cms/assignments/{assignment.id}/',
                    is_read=i < 5,
                    read_at=timezone.now() if i < 5 else None,
                    created_by=admin,
                ),
            )

        # ─── 5 NOTICES ───
        for title, content in NOTICES:
            created = Notice.objects.get_or_create(
                title=title,
                defaults=dict(content=content, is_active=True, created_by=admin),
            )[1]
            self.stdout.write(f'  [{"NEW" if created else "SKIP"}] Notice: {title[:50]}')

        # ─── WELCOME NOTIFICATIONS ───
        for u in users[1:]:
            Notification.objects.get_or_create(
                recipient=u,
                notification_type='welcome',
                title='Welcome',
                defaults=dict(
                    message=f'{u.full_name}, welcome to Content Tracker! Your account is active.',
                    is_read=True,
                    read_at=timezone.now(),
                    created_by=admin,
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            '\n  === Seed data complete! 10 sets created. ===\n'
            '  Admin:    username=admin    / password=admin123\n'
            '  Reporter: username=reporter01..10 / password=reporter123'
        ))
