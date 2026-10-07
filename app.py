# ==========================================================
#  LegendMart - MLBB Account Marketplace
#  Updated: Supabase + PostgreSQL support fixed
# ==========================================================
import os
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---------- CONFIG ----------
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'jolobarbin267@gmail.com')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123')
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-deploy')

# Database: SQLite locally, PostgreSQL/Supabase on Render
database_url = os.environ.get('DATABASE_URL', 'sqlite:///legendmart.db')

if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if 'postgresql://' in database_url and 'sslmode=' not in database_url:
    separator = '&' if '?' in database_url else '?'
    database_url = f"{database_url}{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

RANKS = ['Warrior', 'Elite', 'Master', 'Grandmaster', 'Epic',
         'Legend', 'Mythic', 'Mythic Honor', 'Mythic Glory', 'Mythic Immortal']

STATUS_PENDING = 'pending'
STATUS_APPROVED = 'approved'
STATUS_DECLINED = 'declined'

# ==========================================================
#  DATABASE MODELS
# ==========================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    gcash = db.Column(db.String(50))
    maya = db.Column(db.String(50))
    paypal = db.Column(db.String(100))
    id_type = db.Column(db.String(50), nullable=False)
    id_number = db.Column(db.String(100), nullable=False)
    id_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    listings = db.relationship('Listing', backref='seller', lazy=True,
                               cascade='all, delete-orphan')

    @property
    def is_admin(self):
        return self.email == ADMIN_EMAIL

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    skin_count = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    images = db.Column(db.Text)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def image_list(self):
        if self.images:
            return [i for i in self.images.split(',') if i]
        return []

    @property
    def cover_image(self):
        imgs = self.image_list
        return imgs[0] if imgs else None

    @property
    def status_badge(self):
        return {
            STATUS_PENDING: ('Pending', 'gold'),
            STATUS_APPROVED: ('Approved', 'green'),
            STATUS_DECLINED: ('Declined', 'red'),
        }.get(self.status, (self.status, 'gray'))

# Create tables + auto-create admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email=ADMIN_EMAIL).first():
        admin = User(
            fullname="Administrator",
            email=ADMIN_EMAIL,
            address="LegendMart HQ",
            id_type="National ID",
            id_number="ADMIN-0001",
        )
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"[*] Admin account created -> {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

# ==========================================================
#  HELPERS
# ==========================================================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            flash('Admin access only.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrap

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.context_processor
def inject_globals():
    user = current_user()
    pending_count = 0
    if user and user.is_admin:
        pending_count = Listing.query.filter_by(status=STATUS_PENDING).count()
    return dict(current_user=user, ranks=RANKS, pending_count=pending_count)

def save_images(file_list, prefix):
    saved = []
    ts = int(datetime.utcnow().timestamp())
    for idx, f in enumerate(file_list):
        if f and f.filename and allowed_file(f.filename):
            fname = secure_filename(f"{prefix}_{ts}_{idx}_{f.filename}")
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            saved.append(fname)
    return ','.join(saved)

def delete_listing_images(listing):
    for img in listing.image_list:
        p = os.path.join(app.config['UPLOAD_FOLDER'], img)
        if os.path.exists(p):
            os.remove(p)

# ==========================================================
#  PUBLIC ROUTES
# ==========================================================
@app.route("/")
def home():
    latest = Listing.query.filter_by(status=STATUS_APPROVED) \
        .order_by(Listing.created_at.desc()).limit(4).all()
    return render_template("home.html", latest=latest)

@app.route("/browse")
def browse():
    search = request.args.get('search', '').strip()
    rank_filter = request.args.get('rank', '').strip()
    max_price = request.args.get('max_price', '').strip()
    q = Listing.query.filter_by(status=STATUS_APPROVED)
    if search:
        q = q.filter(Listing.title.contains(search) | Listing.description.contains(search))
    if rank_filter:
        q = q.filter_by(rank=rank_filter)
    if max_price:
        try:
            q = q.filter(Listing.price <= float(max_price))
        except ValueError:
            pass
    listings = q.order_by(Listing.created_at.desc()).all()
    return render_template("browse.html", listings=listings,
                           search=search, rank_filter=rank_filter, max_price=max_price)

@app.route("/account/<int:listing_id>")
def account_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    user = current_user()
    if listing.status != STATUS_APPROVED:
        if not (user and (user.is_admin or user.id == listing.seller_id)):
            abort(404)
    return render_template("account_detail.html", listing=listing, seller=listing.seller)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ==========================================================
#  AUTH ROUTES
# ==========================================================
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        address = request.form.get('address', '').strip()
        gcash = request.form.get('gcash', '').strip()
        maya = request.form.get('maya', '').strip()
        paypal = request.form.get('paypal', '').strip().lower()
        id_type = request.form.get('id_type', '').strip()
        id_number = request.form.get('id_number', '').strip()

        if not all([fullname, email, password, address, id_type, id_number]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))
        if not (gcash or maya or paypal):
            flash('Please provide at least one payment method (GCash, Maya, or PayPal).', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('register'))

        id_image_filename = None
        if 'id_image' in request.files:
            f = request.files['id_image']
            if f and f.filename and allowed_file(f.filename):
                id_image_filename = secure_filename(f"id_{email}_{int(datetime.utcnow().timestamp())}_{f.filename}")
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], id_image_filename))
            elif f and f.filename:
                flash('ID picture must be png, jpg, gif, or pdf.', 'error')
                return redirect(url_for('register'))

        user = User(fullname=fullname, email=email, address=address,
                    gcash=gcash, maya=maya, paypal=paypal,
                    id_type=id_type, id_number=id_number, id_image=id_image_filename)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        flash(f'Registration successful! Welcome, {fullname}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash(f'Welcome back, {user.fullname}!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ==========================================================
#  SELLER DASHBOARD
# ==========================================================
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user.is_admin:
        return redirect(url_for('admin_dashboard'))
    my_listings = Listing.query.filter_by(seller_id=user.id) \
        .order_by(Listing.created_at.desc()).all()
    return render_template("dashboard.html", user=user, listings=my_listings)

@app.route("/sell", methods=['GET', 'POST'])
@login_required
def sell():
    user = current_user()
    if user.is_admin:
        flash('Admins do not sell accounts.', 'info')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        rank = request.form.get('rank', '').strip()
        try:
            skin_count = int(request.form.get('skin_count', '0'))
            price = float(request.form.get('price', '0'))
        except ValueError:
            flash('Skin count and price must be numbers.', 'error')
            return redirect(url_for('sell'))
        description = request.form.get('description', '').strip()
        if not (title and rank and price > 0):
            flash('Please fill in title, rank, and price.', 'error')
            return redirect(url_for('sell'))
        files = request.files.getlist('images')[:5]
        images_str = save_images(files, f"listing_{user.id}")
        listing = Listing(seller_id=user.id, title=title, rank=rank,
                          skin_count=skin_count, price=price,
                          description=description, images=images_str,
                          status=STATUS_PENDING)
        db.session.add(listing)
        db.session.commit()
        flash('Your account has been submitted and is pending admin approval.', 'success')
        return redirect(url_for('dashboard'))
    return render_template("sell.html")

@app.route("/edit/<int:listing_id>", methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    user = current_user()
    if listing.seller_id != user.id and not user.is_admin:
        abort(403)
    if request.method == 'POST':
        listing.title = request.form.get('title', '').strip()
        listing.rank = request.form.get('rank', '').strip()
        try:
            listing.skin_count = int(request.form.get('skin_count', '0'))
            listing.price = float(request.form.get('price', '0'))
        except ValueError:
            flash('Skin count and price must be numbers.', 'error')
            return redirect(url_for('edit_listing', listing_id=listing.id))
        listing.description = request.form.get('description', '').strip()
        files = request.files.getlist('images')[:5]
        if files and files[0].filename:
            delete_listing_images(listing)
            listing.images = save_images(files, f"listing_{user.id}")
        if not user.is_admin:
            listing.status = STATUS_PENDING
            flash('Listing updated and sent back for admin approval.', 'success')
        else:
            flash('Listing updated.', 'success')
        db.session.commit()
        return redirect(url_for('dashboard') if not user.is_admin else url_for('admin_dashboard'))
    return render_template("edit_listing.html", listing=listing)

@app.route("/delete/<int:listing_id>", methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    user = current_user()
    if listing.seller_id != user.id and not user.is_admin:
        abort(403)
    delete_listing_images(listing)
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted.', 'info')
    return redirect(url_for('dashboard') if not user.is_admin else url_for('admin_dashboard'))

# ==========================================================
#  ADMIN ROUTES
# ==========================================================
@app.route("/admin")
@admin_required
def admin_dashboard():
    pending = Listing.query.filter_by(status=STATUS_PENDING) \
        .order_by(Listing.created_at.desc()).all()
    approved = Listing.query.filter_by(status=STATUS_APPROVED) \
        .order_by(Listing.created_at.desc()).all()
    declined = Listing.query.filter_by(status=STATUS_DECLINED) \
        .order_by(Listing.created_at.desc()).all()
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_dashboard.html",
                           pending=pending, approved=approved, declined=declined, users=users)

@app.route("/admin/approve/<int:listing_id>", methods=['POST'])
@admin_required
def admin_approve(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = STATUS_APPROVED
    db.session.commit()
    flash(f'Listing "{listing.title}" has been approved and is now live.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/decline/<int:listing_id>", methods=['POST'])
@admin_required
def admin_decline(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = STATUS_DECLINED
    db.session.commit()
    flash(f'Listing "{listing.title}" has been declined.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete-listing/<int:listing_id>", methods=['POST'])
@admin_required
def admin_delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    delete_listing_images(listing)
    db.session.delete(listing)
    db.session.commit()
    flash('Listing permanently deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete-user/<int:user_id>", methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete the admin account.', 'error')
        return redirect(url_for('admin_dashboard'))
    for listing in user.listings:
        delete_listing_images(listing)
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.fullname}" and all their listings have been deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

# ==========================================================
#  RUN
# ==========================================================
if __name__ == "__main__":
    app.run(debug=False)
