# actionunit/management/commands/create_test_classes.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from actionunit.models import Church, CustomUser, ActionUnitClass, ClassTeacher

class Command(BaseCommand):
    help = 'Create test data for classes and teachers'

    def handle(self, *args, **options):
        # Your test data creation code here
        church = Church.objects.first()
        if not church:
            self.stdout.write(self.style.ERROR("No church found. Please run church signup first."))
            return

   

        def create_test_data():
            # Get the church we created during signup
            church = Church.objects.first()
            if not church:
                print("No church found. Please run church signup first.")
                return

            # Create some teacher users
            teacher1 = CustomUser.objects.create_user(
                username='teacher.james@example.com',
                email='teacher.james@example.com',
                password='teacher123',
                name='Brother James',
                phone='+233123456789',
                role='teacher',
                church=church
            )

            teacher2 = CustomUser.objects.create_user(
                username='teacher.grace@example.com',
                email='teacher.grace@example.com',
                password='teacher123',
                name='Sister Grace',
                phone='+233987654321',
                role='teacher',
                church=church
            )

            teacher3 = CustomUser.objects.create_user(
                username='teacher.samuel@example.com',
                email='teacher.samuel@example.com',
                password='teacher123',
                name='Brother Samuel',
                phone='+233555666777',
                role='teacher',
                church=church
            )

            # Create some classes
            class1 = ActionUnitClass.objects.create(
                church=church,
                name='Youth Action Unit',
                location='Main Church Hall',
                meeting_time=time(9, 30),  # 9:30 AM
                description='Youth Sabbath School class for ages 13-35'
            )

            class2 = ActionUnitClass.objects.create(
                church=church,
                name='Women\'s Fellowship',
                location='Annex Building',
                meeting_time=time(10, 0),  # 10:00 AM
                description='Women\'s Bible study and fellowship'
            )

            class3 = ActionUnitClass.objects.create(
                church=church,
                name='Men\'s Bible Study',
                location='Conference Room',
                meeting_time=time(9, 0),  # 9:00 AM
                description='Men\'s discipleship and Bible study'
            )

            # Assign teachers to classes
            ClassTeacher.objects.create(
                action_unit_class=class1,
                teacher=teacher1
            )

            ClassTeacher.objects.create(
                action_unit_class=class2,
                teacher=teacher2
            )

            ClassTeacher.objects.create(
                action_unit_class=class3,
                teacher=teacher3
            )

            print("Test data created successfully!")
            print(f"Church: {church.name}")
            print(f"Teachers: {teacher1.name}, {teacher2.name}, {teacher3.name}")
            print(f"Classes: {class1.name}, {class2.name}, {class3.name}")

        if __name__ == '__main__':
            create_test_data()
            

        self.stdout.write(self.style.SUCCESS("Test class data created successfully!"))