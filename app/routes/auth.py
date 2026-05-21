import random
from flask import Blueprint, render_template, request, current_app
from getmac import get_mac_address
from app.services.google_sheets import GoogleSheetsService
from app.services.pihole import PiholeService
from app.services.radius import RadiusService
from app.models import RadiusModel

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/link_your_device', methods=['GET', 'POST'])
def link_your_device():
    error = None
    success_data = None
    
    # Auto-detect IP
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip == '::1':
        user_ip = '127.0.0.1'

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        telephone = request.form.get('telephone', '').strip()
        
        # 1. Validate against Sheets API (or local mock database)
        if GoogleSheetsService.validate_student(student_id, telephone):
            
            # 2. Get client MAC address
            mac_address = get_mac_address(ip=user_ip)
            
            # Localhost dev fallback or mock mode MAC generator
            is_local = user_ip in ('127.0.0.1', 'localhost', '::1')
            if (not mac_address or mac_address == '00:00:00:00:00:00') and (current_app.config['MOCK_MODE'] or is_local):
                # Deterministic mock MAC from student ID hash for testing
                seed = sum(ord(c) for c in student_id)
                random.seed(seed)
                mac_address = f"02:AE:CC:{random.randint(10,99)}:{random.randint(10,99)}:{random.randint(10,99)}"
                print(f"[Dev Mode] Mocked MAC {mac_address} for localhost client {user_ip}")
            
            if mac_address and mac_address != -1:
                mac_address = mac_address.upper()
                
                # 3. Register in local database & RADIUS tables
                RadiusService.register_user_device(student_id, telephone, mac_address, user_ip)
                
                # 4. Sync to Pi-hole database group 1
                PiholeService.sync_device_to_pihole(mac_address, action='add')
                
                # 5. Write to legacy file (for compatibility)
                PiholeService.add_to_newly_registered_file(mac_address)
                
                # 6. Simulate RADIUS Accounting connection
                RadiusService.create_mock_acct_session(mac_address, user_ip)
                
                success_data = {
                    'student_id': student_id,
                    'mac_address': mac_address,
                    'ip_address': user_ip,
                    'status': 'Activated'
                }
            else:
                error = "Automatic MAC address detection failed. Please ensure you are connected directly to the AECC Local Area Network."
        else:
            error = "Student ID or phone number verification failed. Please verify your credentials and try again."

    return render_template(
        'link_your_device.html', 
        error=error, 
        success_data=success_data,
        client_ip=user_ip
    )
