import csv

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создает объекты моделей из файлов csv."""

    # python manage.py load_data_from_csv --file_name ingredients.csv
    # --model_name Ingredient --app_name recipes

    help = 'Создает объект модели в базу данных из файла .csv'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file_name',
            type=str,
            help='имя файла',
        )
        parser.add_argument(
            '--model_name',
            type=str,
            help='имя модели',
        )
        parser.add_argument(
            '--app_name',
            type=str,
            help='приложение модели',
        )

    def handle(self, *args, **options):
        file_path = 'static/data/' + options['file_name']
        model = apps.get_model(
            options['app_name'],
            options['model_name'],
        )
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.reader(
                csv_file,
                delimiter=','
            )
            for row in reader:
                object_dict = {
                    'name': row[0],
                    'measurement_unit': row[1],
                }
                model.objects.create(**object_dict)
