from django.core.management.base import BaseCommand
from base.models import State, Country

class Command(BaseCommand):
    help = 'Seeds Indian states'

    def handle(self, *args, **kwargs):
        country_id = 77
        
        try:
            country = Country.objects.get(id=country_id)
        except Country.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Country with id {country_id} does not exist'))
            return

        states_data = [
            {'name': 'Andhra Pradesh', 'code': 'AP'},
            {'name': 'Arunachal Pradesh', 'code': 'AR'},
            {'name': 'Assam', 'code': 'AS'},
            {'name': 'Bihar', 'code': 'BR'},
            {'name': 'Chhattisgarh', 'code': 'CG'},
            {'name': 'Goa', 'code': 'GA'},
            {'name': 'Gujarat', 'code': 'GJ'},
            {'name': 'Haryana', 'code': 'HR'},
            {'name': 'Himachal Pradesh', 'code': 'HP'},
            {'name': 'Jharkhand', 'code': 'JH'},
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Kerala', 'code': 'KL'},
            {'name': 'Madhya Pradesh', 'code': 'MP'},
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Manipur', 'code': 'MN'},
            {'name': 'Meghalaya', 'code': 'ML'},
            {'name': 'Mizoram', 'code': 'MZ'},
            {'name': 'Nagaland', 'code': 'NL'},
            {'name': 'Odisha', 'code': 'OR'},
            {'name': 'Punjab', 'code': 'PB'},
            {'name': 'Rajasthan', 'code': 'RJ'},
            {'name': 'Sikkim', 'code': 'SK'},
            {'name': 'Tamil Nadu', 'code': 'TN'},
            {'name': 'Telangana', 'code': 'TG'},
            {'name': 'Tripura', 'code': 'TR'},
            {'name': 'Uttar Pradesh', 'code': 'UP'},
            {'name': 'Uttarakhand', 'code': 'UK'},
            {'name': 'West Bengal', 'code': 'WB'},
            # Union Territories
            {'name': 'Andaman and Nicobar Islands', 'code': 'AN'},
            {'name': 'Chandigarh', 'code': 'CH'},
            {'name': 'Dadra and Nagar Haveli and Daman and Diu', 'code': 'DH'},
            {'name': 'Delhi', 'code': 'DL'},
            {'name': 'Jammu and Kashmir', 'code': 'JK'},
            {'name': 'Ladakh', 'code': 'LA'},
            {'name': 'Lakshadweep', 'code': 'LD'},
            {'name': 'Puducherry', 'code': 'PY'},
        ]

        created_count = 0
        updated_count = 0

        for state_data in states_data:
            state, created = State.objects.update_or_create(
                name=state_data['name'],
                country=country,
                defaults={'code': state_data['code']}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {state.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {state.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding completed: {created_count} created, {updated_count} updated'
        ))