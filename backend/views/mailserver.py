from flask_mail import Message
from extensions import mail
import os
from tasks import send_celery_email

def email(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = 'demajor45@gmail.com'
    app.config['MAIL_PASSWORD'] = 'wnpc ygqz xnzm ckia'
    app.config['MAIL_DEFAULT_SENDER'] = 'demajor45@gmail.com'
    
    mail.init_app(app)

def send_email(name, email):
    subject = "Welcome to The Shop"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #fff0f5; color: #3a0c1a; padding: 20px; line-height: 1.6;">
            <h2 style="color: #d6336c; margin-bottom: 25px;">Hello {name}, Welcome to The Shop!</h2>
            
            <p style="margin-bottom: 20px; font-size: 16px;">
                Thank you for joining <strong>The Shop</strong> — your one-stop shop for quality products.
            </p>
            
            <p style="margin-bottom: 15px; font-size: 16px;">With us, you can:</p>
            
            <ul style="margin-bottom: 25px; padding-left: 20px;">
                <li style="margin-bottom: 10px; font-size: 16px;">Shop handpicked skincare, makeup, and haircare collections</li>
                <li style="margin-bottom: 10px; font-size: 16px;">Enjoy exclusive offers and Free shipping on orders above kes 1500</li>
                <li style="margin-bottom: 10px; font-size: 16px;">Shop happily with a beautiful and secure experience</li>
            </ul>
            
            <p style="margin-bottom: 25px; font-size: 16px;">Ready to look stunning?</p>
            
            <div style="margin: 30px 0;">
                <a href="https://the-shop-opal.vercel.app/" 
                   style="background-color: #e11d48; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                   Start Shopping
                </a>
            </div>
            
            <p style="margin-top: 40px; font-size: 16px;">
                With love,<br/>
                <strong>The Shop Team </strong>
            </p>
        </body>
    </html>
    """
    
    text_body = f"""
    Hello {name},
    
    Welcome to The Shop — your one-stop shop for the best products!
    
    Here's what you can expect:
    - Explore handpicked skincare, makeup, and haircare
    - Get exclusive offers
    - Enjoy a smooth shopping experience
    
    Start shopping now: https://the-shop-opal.vercel.app/
    With love,
    The Shop Team 
    """
    
    send_celery_email.delay(subject, [email], html_body, text_body)

def send_reset_email(email, reset_url):
    subject = "Reset Your Password - The Shop"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #fff0f5; color: #3a0c1a; padding: 20px; line-height: 1.6;">
            <h2 style="color: #d6336c; margin-bottom: 25px;">Reset Your Password</h2>
            
            <p style="margin-bottom: 20px; font-size: 16px;">Hi there 👋,</p>
            
            <p style="margin-bottom: 20px; font-size: 16px;">
                We received a request to reset the password for your account associated with <strong>{email}</strong>.
            </p>
            
            <p style="margin-bottom: 25px; font-size: 16px;">Click the button below to reset it:</p>
            
            <div style="margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #be123c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                   Reset Password
                </a>
            </div>
            
            <p style="margin: 25px 0; font-size: 16px; color: #666;">
                This link will expire in 1 hour.
            </p>
            
            <p style="margin-bottom: 30px; font-size: 16px;">
                If you didn't request a reset, you can safely ignore this email.
            </p>
            
            <p style="margin-top: 40px; font-size: 16px;">
                With care,<br/>
                <strong>The Shop Team </strong>
            </p>
        </body>
    </html>
    """
    
    text_body = f"""
    Hello,
    
    You requested a password reset for your The Shop account ({email}).
    
    Click the link below to reset it:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this reset, you can ignore this email.
    
    With care,
    The Shop Team 
    """
    
    send_celery_email.delay(subject, [email], html_body, text_body)

def send_order_confirmation_email(name, email, order):     

    subject = f"Order Confirmation - #{order['id']} | The Shop"      
    

    html_items = ''.join(f"<li>{item['quantity']} x {item['name']} - Ksh {item['price']:.2f} each = Ksh {(item['price'] * item['quantity']):.2f}</li>" for item in order['items'])          
    
    newline = '\n'
    text_items = ''.join(f"- {item['quantity']} x {item['name']} - Ksh {item['price']:.2f} each = Ksh {(item['price'] * item['quantity']):.2f}{newline}" for item in order['items'])      


    subtotal = sum(item['price'] * item['quantity'] for item in order['items'])
    shipping_cost = order.get('shipping_cost', 0)
    
    html_body = f"""     
    <html>         
        <body style="font-family: Arial, sans-serif; background-color: #ffffff; color: #3a0c1a; padding: 20px; line-height: 1.6;">             
            <h2 style="color: #d6336c;">Hi {name}, your order is confirmed! </h2>                          
            
            <p>Thank you for shopping with <strong>The Shop</strong>. We're thrilled to get started on your order.</p>                          
            
            <p><strong>Order ID:</strong> {order['id']}<br/>                
            <strong>Invoice:</strong> {order.get('invoice_number', f"INV-{order['id']}")}<br/>
            <strong>Payment Method:</strong> {order.get('payment_method', 'M-Pesa').upper()}<br/>
            <strong>Total:</strong> Ksh {order['total']:.2f}</p>                          
            
                          
            
            <h3 style="margin-top: 30px;">Order Items:</h3>             
            <ul>                 
                {html_items}             
            </ul>
            
            <h3>Payment Summary:</h3>
            <p><strong>Subtotal:</strong> Ksh {subtotal:.2f}<br/>
            <strong>Shipping:</strong> {('FREE' if shipping_cost == 0 else f'Ksh {shipping_cost:.2f}')}<br/>
            <strong>Total Paid:</strong> Ksh {order['total']:.2f}</p>              
            
            <p style="margin-top: 30px;">We'll notify you once it ships. Estimated delivery is 1-3 days. Meanwhile, you can track your order anytime from your account.</p>              
            
           <div style="margin-top: 40px;">                 
    <a href="https://the-shop-opal.vercel.app/{order['id']}"                     
       style="background-color: #e11d48; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold;">                    
        View Order                 
    </a>             
</div>
            <p style="margin-top: 30px; font-size: 14px; color: #666;">
            Need help? Contact us:<br/>
            Email: info@theshop.com<br/>
            Phone: +254 721 400 997
            </p>              
            
        </body>     
    </html>     
    """      

    text_body = f"""Hi {name},  

Thanks for your order with The Shop!  

Order ID: {order['id']} 
Invoice: {order.get('invoice_number', f"INV-{order['id']}")} 
Payment Method: {order.get('payment_method', 'M-Pesa').upper()}
Total: Ksh {order['total']:.2f}  



Items: 
{text_items}

Payment Summary:
Subtotal: Ksh {subtotal:.2f}
Shipping: {('FREE' if shipping_cost == 0 else f'Ksh {shipping_cost:.2f}')}
Total Paid: Ksh {order['total']:.2f}

Estimated delivery: 1-3 days

You can view your order here: https://the-shop.app/{order['id']}  

Need help? 
Email: support@theshop.co.ke
Phone: +254 700 000 000

With love, 
The Shop Team 💖"""      

    send_celery_email.delay(subject, [email], html_body, text_body)

def send_manager_invite_email(name, email, is_existing_user=False, password=None):

    subject = "You've Been Added as a Manager - The Shop"

    if is_existing_user:
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #fff0f5; color: #3a0c1a; padding: 20px; line-height: 1.6;">
                <h2 style="color: #d6336c;">Hi {name},</h2>
                <p>We're excited to let you know that you've been granted <strong>Manager Access</strong> on <strong>The Shop</strong>.</p>
                <p>You can now log in and manage orders and products directly from the admin panel.</p>
                <div style="margin: 30px 0;">
                    <a href="https://the-shop-opal.vercel.app/login"
                       style="background-color: #e11d48; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                       Login
                    </a>
                </div>
                <p style="margin-top: 40px;">With love,<br/>The Shop Team 💖</p>
            </body>
        </html>
        """

        text_body = f"""Hi {name},

You've been promoted to Manager on The Shop platform!

You can now log in and manage products and orders here:
https://the-shop-opal.vercel.app/login

With love,
The Shop Team 💖
"""
    else:
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #fff0f5; color: #3a0c1a; padding: 20px; line-height: 1.6;">
                <h2 style="color: #d6336c;">Welcome {name}!</h2>
                <p>You've been added as a <strong>Manager</strong> on <strong>The Shop</strong>.</p>
                <p>Your login details are:</p>
                <ul>
                    <li><strong>Email:</strong> {email}</li>
                    <li><strong>Password:</strong> {password}</li>
                </ul>
                <p>We recommend changing your password after first login.</p>
                <div style="margin: 30px 0;">
                    <a href="https://the-shop-opal.vercel.app/login"
                       style="background-color: #e11d48; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                       Log In as Manager
                    </a>
                </div>
                <p style="margin-top: 40px;">With love,<br/>The Shop Team 💖</p>
            </body>
        </html>
        """

        text_body = f"""Welcome {name}!

You've been added as a Manager on The Shop.

Login with:
Email: {email}
Password: {password}


Access the admin dashboard here: https://the-shop-opal.vercel.app/login

With love,
The Shop Team 💖
"""

    send_celery_email.delay(subject, [email], html_body, text_body)
