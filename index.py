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
        else:
            return render_template("search.html", opc = True, name = name )
    else:
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
            server.login('apapachatestore@gmail.com','apapachatecontrasena')
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
    server.login('apapachatestore@gmail.com','apapachatecontrasena')
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
        print(pa)
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
        server.login('apapachatestore@gmail.com','apapachatecontrasena')
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
                    server.login('apapachatestore@gmail.com','apapachatecontrasena')
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

@app.route("/adduser", methods=['POST'])
def adduser():
    flash('Usuario registrado satisfactoriamente')
    return redirect(url_for('storeManager'))


#apapachateStore
@app.route("/")
def index():
    productos = db.get("Productos", "")
    return render_template('index.html', productos = productos)

@app.route("/productos", methods = ['GET', 'POST'])
def product():
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

@app.route("/addproduct/<int:precio>")
def agregar(precio):
    if 'total' in session:
        session['total'] = int(escape(session['total']))+precio
    else:
        session['total'] = precio
    flash('El total es {}'.format(escape(session['total'])))
    return redirect(url_for('product'))


@app.route("/successful")
def successful():
    return render_template("successful.html")

@app.route("/carrito")
def carrito():
    if 'total' in session:
        return render_template('carrito.html', total = escape(session['total']))
    else:
        return render_template('carrito.html')

@app.route("/producto/<id>")
def producto(id):
    producto = db.get("Productos", id)
    return render_template("producto.html", productos = producto, id = id)

@app.route("/succesfulPayment")
def succesfulPayment():
    session.pop("total")
    return render_template('successful.html')

@app.route("/cancelledPayment")
def cancelledPayment():
    return render_template('cancel.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
  sess = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
      'price_data': {
        'currency': 'mxn',
        'product_data': {
          'name': 'T-shirt',
        },
        'unit_amount': int(escape(session['total']))*100,
      },
      'quantity': 1,
    }],
    mode='payment',
    success_url='http://apapachatestore.herokuapp.com/succesfulPayment',
    cancel_url='http://apapachatestore.herokuapp.com/cancelledPayment',
  )
  return jsonify(id=sess.id)

if __name__ == '__main__': 
    app.run(debug=True, port=5500)
