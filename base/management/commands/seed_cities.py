from django.core.management.base import BaseCommand
from base.models import City, State

class Command(BaseCommand):
    help = 'Seeds Indian cities'

    def handle(self, *args, **kwargs):
        # Cities data organized by state code
        cities_data = {
            'AP': [  # Andhra Pradesh
                'Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore', 'Kurnool',
                'Rajahmundry', 'Kakinada', 'Tirupati', 'Anantapur', 'Kadapa',
                'Vizianagaram', 'Eluru', 'Ongole', 'Nandyal', 'Machilipatnam',
                'Adoni', 'Tenali', 'Chittoor', 'Hindupur', 'Proddatur'
            ],
            'AR': [  # Arunachal Pradesh
                'Itanagar', 'Naharlagun', 'Pasighat', 'Tawang', 'Ziro',
                'Bomdila', 'Tezu', 'Roing', 'Changlang', 'Along'
            ],
            'AS': [  # Assam
                'Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon',
                'Tinsukia', 'Tezpur', 'Bongaigaon', 'Diphu', 'Dhubri',
                'North Lakhimpur', 'Karimganj', 'Sivasagar', 'Goalpara', 'Barpeta'
            ],
            'BR': [  # Bihar
                'Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Darbhanga',
                'Purnia', 'Bihar Sharif', 'Arrah', 'Begusarai', 'Katihar',
                'Munger', 'Chhapra', 'Saharsa', 'Sasaram', 'Hajipur',
                'Dehri', 'Siwan', 'Motihari', 'Nawada', 'Buxar'
            ],
            'CG': [  # Chhattisgarh
                'Raipur', 'Bhilai', 'Bilaspur', 'Korba', 'Durg',
                'Rajnandgaon', 'Jagdalpur', 'Raigarh', 'Ambikapur', 'Dhamtari',
                'Mahasamund', 'Chirmiri', 'Bhatapara', 'Dalli-Rajhara', 'Naila Janjgir'
            ],
            'GA': [  # Goa
                'Panaji', 'Margao', 'Vasco da Gama', 'Mapusa', 'Ponda',
                'Bicholim', 'Curchorem', 'Sanquelim', 'Cuncolim', 'Quepem'
            ],
            'GJ': [  # Gujarat
                'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar',
                'Jamnagar', 'Junagadh', 'Gandhinagar', 'Anand', 'Nadiad',
                'Morbi', 'Surendranagar', 'Bharuch', 'Mehsana', 'Bhuj',
                'Porbandar', 'Palanpur', 'Valsad', 'Vapi', 'Navsari',
                'Veraval', 'Godhra', 'Patan', 'Kalol', 'Dahod'
            ],
            'HR': [  # Haryana
                'Faridabad', 'Gurgaon', 'Hisar', 'Rohtak', 'Panipat',
                'Karnal', 'Sonipat', 'Yamunanagar', 'Panchkula', 'Bhiwani',
                'Ambala', 'Sirsa', 'Bahadurgarh', 'Jind', 'Thanesar',
                'Kaithal', 'Rewari', 'Palwal', 'Gohana', 'Hansi'
            ],
            'HP': [  # Himachal Pradesh
                'Shimla', 'Dharamshala', 'Solan', 'Mandi', 'Palampur',
                'Kullu', 'Baddi', 'Nahan', 'Sundernagar', 'Una',
                'Hamirpur', 'Bilaspur', 'Chamba', 'Kangra', 'Parwanoo'
            ],
            'JH': [  # Jharkhand
                'Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro Steel City', 'Deoghar',
                'Phusro', 'Hazaribagh', 'Giridih', 'Ramgarh', 'Medininagar',
                'Chirkunda', 'Dumka', 'Saunda', 'Sahibganj', 'Jhumri Tilaiya'
            ],
            'KA': [  # Karnataka
                'Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum',
                'Dharwad', 'Gulbarga', 'Bellary', 'Bijapur', 'Shimoga',
                'Tumkur', 'Raichur', 'Bidar', 'Hospet', 'Davangere',
                'Hassan', 'Chitradurga', 'Mandya', 'Udupi', 'Kolar',
                'Bagalkot', 'Gadag', 'Robertson Pet', 'Bhadravati', 'Ranibennur'
            ],
            'KL': [  # Kerala
                'Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Kollam', 'Thrissur',
                'Kannur', 'Alappuzha', 'Kottayam', 'Palakkad', 'Malappuram',
                'Manjeri', 'Thalassery', 'Ponnani', 'Vatakara', 'Kanhangad',
                'Kayamkulam', 'Nedumangad', 'Kannur Cantonment', 'Kasaragod', 'Kunnamkulam'
            ],
            'MP': [  # Madhya Pradesh
                'Indore', 'Bhopal', 'Jabalpur', 'Gwalior', 'Ujjain',
                'Sagar', 'Dewas', 'Satna', 'Ratlam', 'Rewa',
                'Katni', 'Singrauli', 'Burhanpur', 'Khandwa', 'Morena',
                'Bhind', 'Chhindwara', 'Guna', 'Shivpuri', 'Vidisha',
                'Damoh', 'Mandsaur', 'Khargone', 'Neemuch', 'Pithampur'
            ],
            'MH': [  # Maharashtra
                'Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik',
                'Aurangabad', 'Solapur', 'Amravati', 'Kolhapur', 'Sangli',
                'Jalgaon', 'Akola', 'Latur', 'Dhule', 'Ahmednagar',
                'Chandrapur', 'Parbhani', 'Ichalkaranji', 'Jalna', 'Ambarnath',
                'Bhiwandi', 'Panvel', 'Nanded', 'Satara', 'Beed',
                'Yavatmal', 'Kamptee', 'Gondia', 'Barshi', 'Wardha'
            ],
            'MN': [  # Manipur
                'Imphal', 'Thoubal', 'Bishnupur', 'Churachandpur', 'Kakching',
                'Ukhrul', 'Senapati', 'Tamenglong', 'Jiribam', 'Moreh'
            ],
            'ML': [  # Meghalaya
                'Shillong', 'Tura', 'Nongstoin', 'Jowai', 'Baghmara',
                'Nongpoh', 'Williamnagar', 'Resubelpara', 'Mairang', 'Cherrapunji'
            ],
            'MZ': [  # Mizoram
                'Aizawl', 'Lunglei', 'Champhai', 'Serchhip', 'Kolasib',
                'Saiha', 'Lawngtlai', 'Mamit', 'Hnahthial', 'Saitual'
            ],
            'NL': [  # Nagaland
                'Kohima', 'Dimapur', 'Mokokchung', 'Tuensang', 'Wokha',
                'Zunheboto', 'Phek', 'Mon', 'Longleng', 'Kiphire'
            ],
            'OR': [  # Odisha
                'Bhubaneswar', 'Cuttack', 'Rourkela', 'Brahmapur', 'Sambalpur',
                'Puri', 'Balasore', 'Bhadrak', 'Baripada', 'Jharsuguda',
                'Bargarh', 'Jeypore', 'Balangir', 'Bhawanipatna', 'Rayagada',
                'Angul', 'Dhenkanal', 'Kendujhar', 'Paradip', 'Barbil'
            ],
            'PB': [  # Punjab
                'Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda',
                'Mohali', 'Hoshiarpur', 'Batala', 'Pathankot', 'Moga',
                'Abohar', 'Malerkotla', 'Khanna', 'Phagwara', 'Muktsar',
                'Barnala', 'Rajpura', 'Firozpur', 'Kapurthala', 'Faridkot'
            ],
            'RJ': [  # Rajasthan
                'Jaipur', 'Jodhpur', 'Kota', 'Bikaner', 'Ajmer',
                'Udaipur', 'Bhilwara', 'Alwar', 'Bharatpur', 'Sikar',
                'Pali', 'Sri Ganganagar', 'Kishangarh', 'Tonk', 'Beawar',
                'Hanumangarh', 'Churu', 'Jhunjhunu', 'Barmer', 'Nagaur',
                'Chittorgarh', 'Sawai Madhopur', 'Makrana', 'Fatehpur', 'Banswara'
            ],
            'SK': [  # Sikkim
                'Gangtok', 'Namchi', 'Gyalshing', 'Mangan', 'Rangpo',
                'Jorethang', 'Singtam', 'Ravangla', 'Pelling', 'Yuksom'
            ],
            'TN': [  # Tamil Nadu
                'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem',
                'Tirunelveli', 'Tiruppur', 'Ranipet', 'Nagercoil', 'Thanjavur',
                'Vellore', 'Kancheepuram', 'Erode', 'Tiruvannamalai', 'Pollachi',
                'Rajapalayam', 'Sivakasi', 'Pudukkottai', 'Neyveli', 'Nagapattinam',
                'Viluppuram', 'Tiruvottiyur', 'Ambattur', 'Pallavaram', 'Tambaram',
                'Avadi', 'Kumbakonam', 'Dindigul', 'Cuddalore', 'Karur'
            ],
            'TG': [  # Telangana
                'Hyderabad', 'Warangal', 'Nizamabad', 'Khammam', 'Karimnagar',
                'Ramagundam', 'Mahbubnagar', 'Nalgonda', 'Adilabad', 'Suryapet',
                'Siddipet', 'Miryalaguda', 'Jagtial', 'Mancherial', 'Nirmal',
                'Kothagudem', 'Bodhan', 'Palwancha', 'Tandur', 'Sircilla'
            ],
            'TR': [  # Tripura
                'Agartala', 'Udaipur', 'Dharmanagar', 'Kailasahar', 'Belonia',
                'Khowai', 'Ambassa', 'Teliamura', 'Sabroom', 'Sonamura'
            ],
            'UP': [  # Uttar Pradesh
                'Lucknow', 'Kanpur', 'Ghaziabad', 'Agra', 'Varanasi',
                'Meerut', 'Prayagraj', 'Bareilly', 'Aligarh', 'Moradabad',
                'Saharanpur', 'Gorakhpur', 'Noida', 'Firozabad', 'Jhansi',
                'Muzaffarnagar', 'Mathura', 'Rampur', 'Shahjahanpur', 'Farrukhabad',
                'Maunath Bhanjan', 'Hapur', 'Ayodhya', 'Etawah', 'Mirzapur',
                'Bulandshahr', 'Sambhal', 'Amroha', 'Hardoi', 'Fatehpur',
                'Raebareli', 'Orai', 'Sitapur', 'Bahraich', 'Modinagar',
                'Unnao', 'Jaunpur', 'Lakhimpur', 'Hathras', 'Banda'
            ],
            'UK': [  # Uttarakhand
                'Dehradun', 'Haridwar', 'Roorkee', 'Haldwani', 'Rudrapur',
                'Kashipur', 'Rishikesh', 'Pithoragarh', 'Ramnagar', 'Rudraprayag',
                'Kotdwar', 'Nainital', 'Tehri', 'Almora', 'Pauri'
            ],
            'WB': [  # West Bengal
                'Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri',
                'Bardhaman', 'Malda', 'Baharampur', 'Habra', 'Kharagpur',
                'Shantipur', 'Dankuni', 'Dhulian', 'Ranaghat', 'Haldia',
                'Raiganj', 'Krishnanagar', 'Nabadwip', 'Medinipur', 'Jalpaiguri',
                'Balurghat', 'Basirhat', 'Bankura', 'Chakdaha', 'Darjeeling',
                'Alipurduar', 'Purulia', 'Jangipur', 'Bangaon', 'Cooch Behar'
            ],
            'AN': [  # Andaman and Nicobar Islands
                'Port Blair', 'Diglipur', 'Rangat', 'Mayabunder', 'Car Nicobar',
                'Hut Bay', 'Nancowry', 'Campbell Bay'
            ],
            'CH': [  # Chandigarh
                'Chandigarh'
            ],
            'DH': [  # Dadra and Nagar Haveli and Daman and Diu
                'Daman', 'Diu', 'Silvassa', 'Amli', 'Naroli'
            ],
            'DL': [  # Delhi
                'New Delhi', 'Delhi', 'Dwarka', 'Rohini', 'Pitampura',
                'Janakpuri', 'Karol Bagh', 'Nehru Place', 'Lajpat Nagar', 'Saket',
                'Vasant Kunj', 'Mayur Vihar', 'Preet Vihar', 'Shahdara', 'Narela'
            ],
            'JK': [  # Jammu and Kashmir
                'Srinagar', 'Jammu', 'Anantnag', 'Baramulla', 'Udhampur',
                'Sopore', 'Kathua', 'Punch', 'Rajauri', 'Bandipore',
                'Kulgam', 'Pulwama', 'Kupwara', 'Ganderbal', 'Samba'
            ],
            'LA': [  # Ladakh
                'Leh', 'Kargil', 'Nubra', 'Zanskar', 'Drass'
            ],
            'LD': [  # Lakshadweep
                'Kavaratti', 'Agatti', 'Andrott', 'Amini', 'Minicoy',
                'Kalpeni', 'Kadmat', 'Kiltan', 'Chetlat', 'Bitra'
            ],
            'PY': [  # Puducherry
                'Puducherry', 'Karaikal', 'Mahe', 'Yanam', 'Oulgaret'
            ],
        }

        created_count = 0
        updated_count = 0
        error_count = 0

        for state_code, cities in cities_data.items():
            try:
                # Get state by code
                state = State.objects.get(code=state_code, country_id=77)
                
                for city_name in cities:
                    try:
                        city, created = City.objects.update_or_create(
                            name=city_name,
                            state=state,
                            defaults={}
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(
                            f'Error with city {city_name}, {state_code}: {str(e)}'
                        ))
                
                self.stdout.write(self.style.SUCCESS(
                    f'Processed {len(cities)} cities for {state.name}'
                ))
                
            except State.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'State with code {state_code} not found. Please run state seeder first.'
                ))
                error_count += 1
                continue

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Seeding completed ==='
        ))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Updated: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))