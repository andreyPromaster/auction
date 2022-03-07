from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Create N users'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--number', type=int,
                            help='Input number of users for creating')
        parser.add_argument('-o', '--result_file_path',
                            type=str,
                            help='Output file with created users')

    def handle(self, *args, **options):
        number_of_users = options['number']
        path = options['result_file_path']
        for _ in range(number_of_users):
            generated_password = User.objects.make_random_password()
            user = User.objects.create_user(username=User.objects.make_random_password(),
                                            password=generated_password)
            self.stdout.write(f'User with username {user.username} and '
                              f'password {generated_password} was created')
            with open(path, 'a') as f:
                f.writelines(f'{user.username} {generated_password}\n')
