from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename
from waste_not import load_data_from_csv, detect_common_contaminants, find_unique_materials, greedy_truck_loading, generate_visualization
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process the data
            sites = load_data_from_csv(filepath)
            
            # Store data in session or pass to results
            return redirect(url_for('dashboard', filename=filename))
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Please upload a CSV file')
        return redirect(url_for('index'))

@app.route('/dashboard/<filename>')
def dashboard(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        sites = load_data_from_csv(filepath)
        
        # Run analyses
        common_contaminants = detect_common_contaminants(sites)
        unique_materials = find_unique_materials(sites)
        loaded_batches = greedy_truck_loading(sites)
        
        # Generate visualization
        generate_visualization(sites)
        
        # Convert plot to base64 for web display
        plot_path = 'waste_materials_venn_diagram.png'
        plot_base64 = None
        if os.path.exists(plot_path):
            with open(plot_path, 'rb') as img_file:
                plot_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Prepare summary statistics
        total_sites = len(sites)
        total_weight = sum(site['total_weight_kg'] for site in sites.values())
        avg_contamination = sum(site['contamination_pct'] for site in sites.values()) / total_sites
        total_materials = len(set().union(*[site['material_list'] for site in sites.values()]))
        
        return render_template('dashboard.html', 
                             sites=sites,
                             common_contaminants=common_contaminants,
                             unique_materials=unique_materials,
                             loaded_batches=loaded_batches,
                             plot_base64=plot_base64,
                             total_sites=total_sites,
                             total_weight=total_weight,
                             avg_contamination=avg_contamination,
                             total_materials=total_materials,
                             filename=filename)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        if filename == 'truck_loading_manifest.csv':
            return send_file('truck_loading_manifest.csv', as_attachment=True)
        elif filename == 'contaminant_report.txt':
            return send_file('contaminant_report.txt', as_attachment=True)
        elif filename == 'waste_materials_venn_diagram.png':
            return send_file('waste_materials_venn_diagram.png', as_attachment=True)
        else:
            flash('File not found')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/sites/<filename>')
def api_sites(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        sites = load_data_from_csv(filepath)
        return jsonify(sites)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)