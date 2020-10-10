from flask import Flask, render_template, request, redirect, url_for, flash, session, escape, jsonify
import os, smtplib, pyrebase, PIL, stripe
from firebase import firebase 
from PIL import Image

app = Flask(__name__)

# settings
app.secret_key = 'mysecretkey'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(APP_ROOT, 'static/')
total = 0

# stripe
stripe.api_key = 'sk_test_51HU3xZEIyvFHfGwOFfxcJB1T75vwnNPwMaAkqu8dlhWsfi73XartM7rzvP8kGY3n3Rjdtc8XoGiTcs0BoijyChwp00ckcgeEK7'

# firebase
db = firebase.FirebaseApplication("https://apapachatestore.firebaseio.com")

# storage
storageConfig = {
    "apiKey": "AIzaSyBAnc0Oz9Y5WEyjqyH385ue6L_UpkvLtew",
    "authDomain": "apapachatestore.firebaseapp.com",
    "databaseURL": "https://apapachatestore.firebaseio.com",
    "projectId": "apapachatestore",
    "storageBucket": "apapachatestore.appspot.com",
    "messagingSenderId": "529842451934",
    "appId": "1:529842451934:web:9a29de330667b9727ad94f"
}
firebase = pyrebase.initialize_app(storageConfig)
storage = firebase.storage()
pathCloud = "Productos/"

# descarga de archivos
data = db.get("Productos", "")
if(data):
    for key in data:
        pathCloud = "Productos/"+data[key]["Imagen"]
        pathLocal = "static/"+data[key]["Imagen"]
        storage.child(pathCloud).download(pathLocal)

#email smtp
emaillist = ['rayma9829@gmail.com',]
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('apapachatestore@gmail.com','apapachatecontrasena')

#storeManager
@app.route("/storeManager", methods =['POST','GET']) 
def storeManager():
    if "username" in session:
        data = db.get("Productos", "")
        name = escape(session["username"])
        if(data):
            return render_template("storeManager.html", it = data, opc = True, name = name )
        else:
            return render_template("storeManager.html", opc = True, name = name )
    else:
        if request.method == 'POST':
            user = request.form['usuario']
            password = request.form['contrasena']
            usuarios = db.get("Usuarios", "")
            auten = False
            for key in usuarios:
                if usuarios[key]["Usuario"]==user and usuarios[key]["Contraseña"]==password:
                    session["username"] = user
                    auten = True
                    break
        
            if auten == True:   
                data = db.get("Productos", "")
                name = escape(session["username"])
                if(data):
                    for key in data:
                        print(data[key]["Imagen"])
                        pathCloud = "Productos/"+data[key]["Imagen"]
                        pathLocal = "static/"+data[key]["Imagen"]
                        storage.child(pathCloud).download(pathLocal)
                    flash('Bienvenido')
                    return render_template("storeManager.html", it = data, opc = True, name = name)
                else:
                    return render_template("storeManager.html", opc = True, name = name)
            else:
                flash('El usuario o la contraseña son incorrectos')
                return render_template("autenticar.html")
        else:
            return render_template("autenticar.html")

@app.route('/storeManager/logout')
def storeLogout():
    session.pop("username")
    flash('Has cerrado tu sesión')
    return redirect(url_for('storeManager'))

@app.route('/storeManager/search')
def storeSearch():
    if "username" in session:
        data = db.get("Busquedas", "")
        name = escape(session["username"])
        if(data):
            return render_template("search.html", it = data, opc = True, name = name )
        return render_template("search.html", opc = True, name = name )
    return render_template("autenticar.html")

@app.route('/storeManager/pages')
def storePages():
    if "username" in session:
        data = db.get("Pagina", "")
        name = escape(session["username"])
        if(data):
            return render_template("pages.html", it = data, opc = True, name = name )
        return render_template("pages.html", opc = True, name = name )
    return render_template("autenticar.html")

@app.route("/add", methods = ['POST'])
def add():
    if not os.path.isdir(target):
        os.mkdir(target)
    if request.method == 'POST':
        producto = request.form['producto']
        imagen = request.files['imagen']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        inventario = request.form['inventario']
        etiquetas = request.form['etiquetas']
        filename = imagen.filename
        destination = "/".join([target, filename])
        if producto == "" or precio == "" or descripcion=="" or (imagen==None) or inventario == None or etiquetas == "":
            flash('Llena todos los campos correctamente')
            return redirect(url_for('storeManager'))
        else:
            filename = imagen.filename
            destination = "/".join([target, filename])
            precioFormat = int(precio)
            imagen.save(destination)
            img = Image.open(destination)
            img = img.resize((600,600))
            img.save(destination)
            pathCloud = "Productos/"+filename
            pathLocal = destination
            storage.child(pathCloud).put(pathLocal)
            data =  {
                    "Producto": producto,
                    "Imagen": filename,
                    "Descripcion": descripcion,
                    "Precio": precio,
                    "Inventario": inventario,
                    "Etiquetas": etiquetas
                    }
            db.post("Productos", data)
            message = 'Se ha agregado un producto satisfactoriamente\nCorreo enviado desde apapachatestore.herokuapp.com'
            subject = 'Producto agregado'
            message = 'Subject: {}\n\n{}'.format(subject, message)
            for email in emaillist:
                server.sendmail('apapachatestore@gmail.com', email, message)
            flash('Producto agregado satisfactoriamente')
            return redirect(url_for('storeManager'))

@app.route("/delete/<id>")
def delete(id):
    img = db.get("Productos", id)["Imagen"]
    print(img)
    db.delete("Productos", id)
    os.remove('static/'+img)
    message = 'El producto ha sido eliminado satisfactoriamente\nCorreo enviado desde apapachatestore.herokuapp.com'
    subject = 'Producto eliminado'
    message = 'Subject: {}\n\n{}'.format(subject, message)
    for email in emaillist:
        server.sendmail('apapachatestore@gmail.com', email, message)
    flash('Producto eliminado satisfactoriamente')
    return redirect(url_for('storeManager'))

@app.route("/edit/<id>")
def edit(id):
    data = db.get("Productos", id)
    print(data)
    return render_template("edit.html", producto = data, id = id)

@app.route("/update/<id>", methods = ['POST'])
def update(id):
    if request.method == 'POST':
        producto = request.form['producto']
        imagen = request.files['imagen']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        inventario = request.form['inventario']
        etiquetas = request.form['etiquetas']
        filename = imagen.filename
        destination = "/".join([target, filename])
        pa = "Productos/"+id
        if imagen:
            img = db.get("Productos", id)["Imagen"]
            os.remove('static/'+img)
            db.put(pa, "Imagen", filename)
            imagen.save(destination)
        if producto:
            db.put(pa, "Producto", producto)
        if descripcion:
            db.put(pa, "Descripcion", descripcion)
        if precio:
            precioFormat = int(precio)
            db.put(pa, "Precio", precioFormat)
        if inventario:
            db.put(pa, "Inventario", inventario)
        if etiquetas:
            db.put(pa, "Etiquetas", etiquetas)
        message = 'El producto ha sido actualizado satisfactoriamente\nCorreo enviado desde apapachatestore.herokuapp.com'
        subject = 'Producto actualizado'
        message = 'Subject: {}\n\n{}'.format(subject, message)
        for email in emaillist:
            server.sendmail('apapachatestore@gmail.com', email, message)
        flash('Producto actualizado satisfactoriamente')
        return redirect(url_for('storeManager'))

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method == 'POST':    
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        confirmcontrasena = request.form['confirmcontrasena']
        correo = request.form['email']
        users = db.get("Usuarios", "")
        registrar = False
        if contrasena == confirmcontrasena:
            for user in users:
                if users[user]["Usuario"] == usuario:
                    flash('El usuario ya existe, intente con otro')
                    return render_template('signup.html')
                else:
                    data =  {
                        "Usuario": usuario,
                        "Contraseña": contrasena,
                        "email": correo
                    }
                    db.post("Usuarios", data)
                    message = 'Se ha registrado un nuevo usuario\nCorreo enviado desde apapachatestore.herokuapp.com'
                    subject = 'Alta de usuario'
                    message = 'Subject: {}\n\n{}'.format(subject, message)
                    for email in emaillist:
                        server.sendmail('apapachatestore@gmail.com', email, message)
                    flash('Usuario registrado exitosamente')
                    return redirect(url_for('storeManager'))
        else:
            flash('Las contraseñas deben coincidir')
            return render_template('signup.html')
    else:
        return render_template('signup.html')

@app.route('/changeName/<name>', methods=['GET', 'POST'])
def changeName(name):
    if request.method == 'POST':
        usuarios = db.get("Usuarios", "")
        password = request.form['password']
        user = request.form['usuario']
        for key in usuarios:
            if usuarios[key]['Usuario'] == name and usuarios[key]['Contraseña'] == password:
                for usuario in usuarios:
                    if usuarios[usuario]['Usuario'] == user:
                        flash('El usuario ya existe')
                        return render_template('changeName_pass.html', name = name)
                ruta = "Usuarios/"+key      
                db.put_async(ruta,'Usuario',user)
                flash('Nombre cambiado satisfactoriamente')
                session['username'] = user
                return redirect(url_for('storeManager'))
        flash('Contraseña incorrecta')
        return render_template('changeName_pass.html', name = name)
    return render_template('changeName_pass.html', name = name)

@app.route('/changePassword/<name>', methods=['GET', 'POST'])
def changePassword(name):
    if request.method == 'POST':
        oldPass = request.form['oldPassword']
        newPass = request.form['newPassword']
        confirmPassword = request.form['confirmPassword']
        usuarios = db.get("Usuarios", "")
        for key in usuarios:
            if usuarios[key]['Usuario'] == name and usuarios[key]['Contraseña'] == oldPass:
                if newPass == confirmPassword:
                    ruta = "Usuarios/"+key
                    db.put_async(ruta, 'Contraseña', newPass)
                    session.pop('username')
                    flash('Contraseña cambiada con exito, debes volver a iniciar sesion')
                    return redirect(url_for('storeManager'))
                flash('Las contraseñas no coinciden')
                return render_template('changePassword.html', name = name)
        flash('Contraseña incorrecta')
        return render_template('changePassword.html', name = name)
    return render_template('changePassword.html', name = name)

#apapachateStore
@app.route("/")
def index():
    pagina = db.get("Pagina", "")
    for key in pagina:
        if pagina[key]['Pagina'] == "Index":        
            n = pagina[key]['Visitas']
            n+=1
            ruta = "Pagina/"+key
            db.put_async(ruta, 'Visitas', n)
    productos = db.get("Productos", "")
    lista = {}
    for key in productos:
        if productos[key]['Etiquetas'] == 'importante':
            lista[key] = productos[key]
    return render_template('index.html', productos = lista)

@app.route("/productos", methods = ['GET', 'POST'])
def product():
    pagina = db.get("Pagina", "")
    for key in pagina:
        if pagina[key]['Pagina'] == "Productos":        
            n = pagina[key]['Visitas']
            n+=1
            ruta = "Pagina/"+key
            db.put_async(ruta, 'Visitas', n)
    productos = {}
    data = db.get("Productos", "")
    if request.method == 'POST':
        search = request.form['search']
        busquedas = db.get("Busquedas", "")
        info = {
            "Busqueda": search,
            "Cantidad": 1
        }
        for key in data:
            if data[key]['Etiquetas'] == search:
                productos[key] = data[key]
        for key in busquedas:
            if busquedas[key]['Busqueda'] == search:
                n = busquedas[key]['Cantidad']
                n+=1
                pa = "Busquedas/"+key
                db.put(pa, "Cantidad", n)
                return render_template("productos.html", productos = productos)
        db.post("Busquedas", info)
        return render_template("productos.html", productos = productos)
    return render_template("productos.html", productos = data)

@app.route("/vaciarCarrito")
def vaciarCarrito():
    session.pop("total")
    flash("Has vaciado el carrito")
    return render_template('carrito.html')

@app.route("/addproduct/<id>/<origen>")
def agregar(id, origen):
    data = db.get("Productos", id)
    precio = int(data['Precio'])
    print(id)
    if 'total' in session:
        items = escape(session['items'])
        items = items+"\n"+id
        session['total'] = int(escape(session['total']))+precio
        session['items'] = items
    else: 
        session['total'] = precio
        session['items'] = id
    flash('El total es {}'.format(escape(session['total'])))
    return redirect(url_for(origen))

@app.route("/carrito")
def carrito():
    pagina = db.get("Pagina", "")
    for key in pagina:
        if pagina[key]['Pagina'] == "Carrito":        
            n = pagina[key]['Visitas']
            n+=1
            ruta = "Pagina/"+key
            db.put_async(ruta, 'Visitas', n)
    if 'total' in session:
        productos = db.get("Productos", "")
        data = str(escape(session['items']))
        dat = data.split(sep='\n')
        return render_template('carrito.html', total = escape(session['total']), items = dat, productos = productos)
    else:
        return render_template('carrito.html')

@app.route("/carritoRemove/<id>")
def carritoRemove(id):
    producto = db.get("Productos", id)
    precio = int(producto['Precio'])
    total = int(escape(session['total']))
    total-=precio
    if total > 0:
        session["total"] = total
        items = str(escape(session['items'])).split(sep='\n')
        items.remove(id)
        session['items'] = str("\n".join(items))
    else:
        session.pop('total')
        session.pop('items')
    flash('Producto eliminado del carrito')
    return redirect(url_for('carrito'))

@app.route("/producto/<id>")
def producto(id):
    producto = db.get("Productos", id)
    return render_template("producto.html", productos = producto, id = id)

@app.route("/succesfulPayment")
def succesfulPayment():
    session.pop("total")
    message = 'Se ha completado una compra, prepara todo para realizar el envio\n\nCorreo enviado desde apapachatestore.herokuapp.com'
    subject = 'Compra completada'
    message = 'Subject: {}\n\n{}'.format(subject, message)
    for email in emaillist:
        server.sendmail('apapachatestore@gmail.com', email, message)
    pagina = db.get("Pagina", "")
    for key in pagina:
        if pagina[key]['Pagina'] == "succesfulPayment":        
            n = pagina[key]['Visitas']
            n+=1
            ruta = "Pagina/"+key
            db.put_async(ruta, 'Visitas', n)
    flash('Pago aplicado correctamente')
    return render_template('successful.html')

@app.route("/cancelledPayment")
def cancelledPayment():
    pagina = db.get("Pagina", "")
    for key in pagina:
        if pagina[key]['Pagina'] == "CancelledPayment":        
            n = pagina[key]['Visitas']
            n+=1
            ruta = "Pagina/"+key
            db.put_async(ruta, 'Visitas', n)
    flash('Pago cancelado')
    return redirect(url_for('carrito'))

@app.route('/payNow/<id>', methods=['POST'])
def payNow(id):
    producto = db.get("Productos", id)
    prod = producto['Producto']
    precio = producto['Precio']
    sess = stripe.checkout.Session.create(
        billing_address_collection='auto',
        shipping_address_collection={
            'allowed_countries': ['MX'],
        },
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'mxn',
                'product_data': {
                    'name': prod,
                },
                'unit_amount': precio*100,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:5500/succesfulPayment',
        cancel_url='http://localhost:5500/productos',
    )
    return jsonify(id=sess.id)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = str(escape(session['items']))
    items = data.split(sep = '\n')
    prod = db.get("Productos", items[0])
    sess = stripe.checkout.Session.create(
        billing_address_collection='auto',
        shipping_address_collection={
            'allowed_countries': ['MX'],
        },
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'mxn',
                'product_data': {
                    'name': prod['Producto'],
                },
                'unit_amount': int(escape(session['total']))*100,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://www.apapachatestore.com/succesfulPayment',
        cancel_url='https://www.apapachatestore.com/cancelledPayment',
    )
    return jsonify(id=sess.id)

if __name__ == '__main__': 
    app.run(debug=True, port=5500)
