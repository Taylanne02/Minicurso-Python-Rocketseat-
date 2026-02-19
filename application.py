from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS #permite que outros sistemas de fora acessem seu sistema
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user #herança para herda o que já é usado no UserMixin



application = Flask(__name__)
application.config['SECRET_KEY'] = "minha_chave_123"
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db' #caminho


login_manager = LoginManager()
db = SQLAlchemy(application) #iniciar a coneção com o banco
login_manager.init_app(application)
login_manager.login_view = 'login'
CORS(application) #permite que outros sistemas de fora acessem seu sistema


#Produto (Id, nome, preço, descrição)
class Product (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False) #Nullable para impedir que fique sem nome
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True) #Text é sem limitação


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable= False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable= False)


#Modelage - Login User(id, username, password)
class User (db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable = False, unique=True)
    password = db.Column(db.String(80), nullable=True) #Por padrão o unique já é falsa
    cart = db.relationship('CartItem', backref='user', lazy=True)


#Autenticação
@login_manager.user_loader 
def load_user(user_id):
    return User.query.get(int(user_id))


@application.route('/')
def initial():
    return 'API up'


@application.route('/login', methods=["POST"])
def login():
    data = request.json
    
    user = User.query.filter_by(username=data.get("username")).first() #filtrar um registro por uma coluna diferente do id
    
    if user and data.get("password") == user.password:
            login_user(user)
            return jsonify({"message": "Logged in sucessfully"})
    
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401


@application.route('/logout', methods = ["POST"])
def logout():
    logout_user()
    return jsonify({"message": "Logout in sucessfully"})



@application.route('/api/products/add', methods=["POST"]) #sinalização de que é uma rota da api, modelo que estamos trabalhando e 
    #depois a operação que está sendo feito (adição no modulo produto). Methodes é a sinalização do que vai ser aceito
@login_required #Bloqueia para somente pessoas autorizadas conseguirem usar
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data["name"], price=data["price"], description=data.get("description", "")) #duas opções que funcionam 
            # =data[""] se não achar dá erro
            # =data.get("") se não achar vai dar o valor que colocar, no caso um texto vazio
        db.session.add(product)
        db.session.commit() #vai mandar pro banco de dados, commit semelhante ao git
        return jsonify({"message": "Product added sucessfully"})
    
    return jsonify({"message": "Invalid product data"}), 400 #dados do produto inválido



@application.route('/api/products/delete/<int:product_id>', methods=["DELETE"]) #Caminhos para o Postman
@login_required
def delete_product(product_id):
    #Recuperar o produto da base de dados
    #Verificar se o produto existe/válido
    #Se existe, apagar da base de dados. Se não existe retornar 404 (não encontrou)
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted sucessfully"})
    
    return jsonify({"message": "Product not found"}), 404 #Quando não encontra



@application.route('/api/products/<int:product_id>', methods=["GET"]) #Caminhos para o Postman
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id: ": product.id,
            "name: ": product.name,
            "price: ": product.price,
            "description: ": product.description
        })
    
    return jsonify({"mensagem": "Product not found"}), 404



@application.route('/api/products/update/<int:product_id>', methods=["PUT"]) #Caminhos para o Postman
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    
    data = request.json 
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']

    if 'description' in data:
        product.description = data['description'] 
    #Essa forma permite alterar uma ou mais, podendo passar só nome ou preço ou descrição.

    db.session.commit()

    return jsonify({"mensagem": "Product updated sucessfully"})      



@application.route('/api/products', methods=["GET"])
def get_product():
    products = Product.query.all() #retorna todos os produtos como uma lista
    product_list = []
    for product in products:
        product_data = {
            "id: ": product.id,
            "name: ": product.name,
            "price: ": product.price, #Não term descrição pois o cliente tem que ir  
                                        #na rota detalhes
        } 
        product_list.append(product_data)
    
    return jsonify(product_list) 

#Checkout
@application.route('/api/cart/add/<int:product_id>', methods=["POST"])
@login_required
def add_to_cart(product_id):
    user = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'mensagem': 'Item added to the cart sucessfully'})

    return jsonify({'mensagem': 'Failed to item to the cart'}), 400


@application.route('/api/cart/remove/<int:product_id>', methods=["DELETE"])
@login_required
def remove_from_cart(product_id):
    cart_item= CartItem.query.filter_by(user_id= current_user.id, product_id= product_id).first() #current para resgatar o usuário logado
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'mensagem': 'Item removed from the cart sucessfully'})
    
    return jsonify({'mensagem': 'Failed to remove item from the cart'}), 400


@application.route('/api/cart', methods=["GET"])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_itens = user.cart
    cart_content=[]
    for cart_item in cart_itens:
        product = Product.query.get(cart_item.product_id)
        cart_content.append({
            "product_name": product.name,
            "id": cart_item.id,
            "user_id": cart_item.user_id,
            "product_id": cart_item.product_id,
            "product_prica": product.price
        })
    return jsonify(cart_content)


@application.route('/api/cart/checkout', methods=["POST"])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_iten in cart_items:
        db.session.delete(cart_iten)
    db.session.commit()

    return jsonify({'mensagem': 'Checkout sucessfully. Cart has been cleared'})





if __name__ == "__main__":
    application.run(debug=True) #Ativando modo depuração, receber mais informações, mais visibilidade com o que está acontecendo com o servidor
