from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from config import Config
from app.models import RadiusModel
from app.services.pihole import PiholeService
from app.services.radius import RadiusService

admin_bp = Blueprint('admin', __name__)

def is_logged_in():
    return session.get('admin_logged_in', False)

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('admin.dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in as administrator.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Invalid administrative credentials.'
            
    return render_template('admin_login.html', error=error)

@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Successfully logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/admin')
@admin_bp.route('/admin/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('admin.login'))
        
    stats = RadiusModel.get_dashboard_stats()
    return render_template('admin_dashboard.html', stats=stats)


# --- Admin API Endpoints ---

@admin_bp.route('/admin/api/stats')
def api_stats():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(RadiusModel.get_dashboard_stats())

@admin_bp.route('/admin/api/devices')
def api_devices():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(RadiusModel.get_all_devices())

@admin_bp.route('/admin/api/logs')
def api_logs():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    
    auth_logs = RadiusModel.get_auth_logs(30)
    sessions = RadiusModel.get_accounting_sessions(30)
    
    return jsonify({
        'auth_logs': auth_logs,
        'sessions': sessions
    })

@admin_bp.route('/admin/api/device/toggle_status', methods=['POST'])
def api_toggle_status():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    student_id = data.get('student_id')
    new_status = data.get('status') # 'Active' or 'Blocked'
    mac_address = data.get('mac_address')
    
    if not student_id or not new_status or not mac_address:
        return jsonify({'error': 'Missing parameters'}), 400
        
    # 1. Update in local db
    RadiusModel.update_device_status(student_id, new_status)
    
    # 2. Sync status to Pi-hole gravity.db
    ph_action = 'add' if new_status == 'Active' else 'remove'
    PiholeService.sync_device_to_pihole(mac_address, action=ph_action)
    
    # 3. Simulate RADIUS log
    auth_pwd = f"AECC-Auth-{student_id[-4:]}"
    if new_status == 'Active':
        RadiusService.log_auth_attempt(mac_address, auth_pwd, 'Access-Accept')
        RadiusService.create_mock_acct_session(mac_address, '192.168.1.150')
    else:
        RadiusService.log_auth_attempt(mac_address, auth_pwd, 'Administrative-Block')
        RadiusService.terminate_mock_sessions(mac_address)
        
    return jsonify({'success': True, 'message': f'Device status updated to {new_status}'})

@admin_bp.route('/admin/api/device/delete', methods=['POST'])
def api_delete_device():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    student_id = data.get('student_id')
    mac_address = data.get('mac_address')
    
    if not student_id or not mac_address:
        return jsonify({'error': 'Missing parameters'}), 400
        
    # Remove from local database and RADIUS credentials
    RadiusModel.delete_device(student_id)
    
    # Remove group mapping in Pi-hole
    PiholeService.sync_device_to_pihole(mac_address, action='remove')
    
    # Terminate any active sessions
    RadiusService.terminate_mock_sessions(mac_address)
    
    return jsonify({'success': True, 'message': 'Device removed successfully'})

@admin_bp.route('/admin/api/device/add', methods=['POST'])
def api_add_device():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    student_id = data.get('student_id', '').strip()
    telephone = data.get('telephone', '').strip()
    mac_address = data.get('mac_address', '').strip().upper()
    
    if not student_id or not telephone or not mac_address:
        return jsonify({'error': 'All fields are required'}), 400
        
    # Register device
    RadiusService.register_user_device(student_id, telephone, mac_address)
    
    # Add to Pi-hole
    PiholeService.sync_device_to_pihole(mac_address, action='add')
    
    # Add to legacy file
    PiholeService.add_to_newly_registered_file(mac_address)
    
    return jsonify({'success': True, 'message': 'Device registered successfully'})

@admin_bp.route('/admin/api/sync_legacy', methods=['POST'])
def api_sync_legacy():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
        
    success = PiholeService.run_legacy_sync()
    if success:
        return jsonify({'success': True, 'message': 'Successfully synchronized legacy Newly_Registered_Members.txt into Pi-hole.'})
    else:
        return jsonify({'error': 'Synchronization failed.'}), 500
