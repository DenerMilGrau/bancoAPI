from flask import Flask, jsonify, redirect, request
from flask_pydantic_spec import FlaskPydanticSpec
from datetime import date
from dateutil.relativedelta import relativedelta
from models import db_session, Livro, Emprestimo, Usuario
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc

app = Flask(__name__)
spec = FlaskPydanticSpec('Flask',
                         title='Flask API',
                         version='1.0.0')
spec.register(app)
app.secret_key = 'chave_secreta'

@app.route('/')
def index():
    return redirect('/livros')
@app.route('/livros', methods=['GET'])
@app.route('/livros/<status>', methods=['GET'])
def get_livros(status=None):
    if status is None:
        lista_livros_sql = select(Livro)
    else:
        if status in ['1', 1, 'True', True]:
            status_emprestimo = True
        elif status in ['0', 0, 'False', False]:
            status_emprestimo = False
        else:
            return jsonify({'result': 'Error. Requisitado uma variável inesperada'}), 400

        lista_livros_sql = select(Livro).where(Livro.status_emprestado == status_emprestimo)

    lista_livros = db_session.execute(lista_livros_sql).scalars()
    result = []
    for livro in lista_livros:
        result.append(livro.serialize_livro())

    return jsonify({'result': result})

@app.route('/usuarios', methods=['GET'])
@app.route('/usuarios/<id_user>', methods=['GET'])
def get_usuarios(id_user=None):
    try:
        if id_user is None:
            sql = select(Usuario)
            sql_executar = db_session.execute(sql).scalars()
            result = []
            for usuario in sql_executar:
                result.append(usuario.serialize_usuario())
            return jsonify({'result': result})
        else:
            id_usuario = int(id_user)
            sql = select(Emprestimo, Usuario, Livro).join(
                Usuario, Emprestimo.ID == Usuario.id).join(
                Livro, Emprestimo.ID_livro == Livro.id_livro
            ).where(Usuario.id == id_usuario)
            sql_executar = db_session.execute(sql).scalars()
            result = []
            for i in sql_executar:
                result.append(i.serialize_emprestimo())
            if result:
                return jsonify({'result': result})
            else:
                return jsonify({'result': 'Não existem dados referente a esse usuario'})

    except ValueError:
        return jsonify({'result': 'Error. Erro de Valor'})


@app.route('/emprestimos', methods=['GET'])
def get_emprestimos():
    lista_emprestimos_sql = select(Emprestimo).join(
        Livro, Emprestimo.ID_livro == Livro.id_livro).join(
        Usuario, Emprestimo.ID == Usuario.id
    )
    lista_emprestimos = db_session.execute(lista_emprestimos_sql).scalars().all()
    print(lista_emprestimos)
    result = []
    for emprestimo in lista_emprestimos:
        result.append(emprestimo.serialize_emprestimo())

    return jsonify({'result': result})

@app.route('/usuarios', methods=['POST'])
def novo_usuario():
    dados_usuario = request.get_json()
    nome = dados_usuario['nome']
    cpf = request.form['cpf']
    telefone = request.form['telefone']
    cpf = str(cpf)
    if not nome or not cpf or not telefone or len(cpf) != 11:
        return jsonify({'result': 'Error. Integrity Error (faltam informações) '}), 400
    else:
        cpf_f = '{0}.{1}.{2}-{3}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])
        post = Usuario(nome=nome, cpf=cpf_f, telefone=telefone)
        post.save()
        db_session.close()
        return jsonify({'result': 'Usuario criado com sucesso!'}), 200

@app.route('/emprestimos', methods=['POST'])
def novo_emprestimo():
    # dados = request.get_json()
    data_emprestimo = request.form['data_emprestimo']
    data_devolucao = request.form['data_devolucao']
    usuario_id = request.form['id_usuario']
    livro_id = request.form['id_livro']

    try:
        if len(data_emprestimo) == 10 or len(data_devolucao) == 10:
            usuario_id = int(usuario_id)
            livro_id = int(livro_id)
            # data formato yyyy-mm-dd
            ano_emprestimo = '{}'.format(data_emprestimo[:4])
            mes_emprestimo = '{}'.format(data_emprestimo[5:7])
            dia_emprestimo = '{}'.format(data_emprestimo[8:])

            ano_devolucao = '{}'.format(data_devolucao[:4])
            mes_devolucao = '{}'.format(data_devolucao[5:7])
            dia_devolucao = '{}'.format(data_devolucao[8:])

            obj_data_emprestimo = date(int(ano_emprestimo), int(mes_emprestimo), int(dia_emprestimo))
            obj_data_devolucao = date(int(ano_devolucao), int(mes_devolucao), int(dia_devolucao))

            delta = obj_data_devolucao - obj_data_emprestimo
            print('delta:', delta, 'delta days:', delta.days)

            if not data_emprestimo or not data_devolucao or not usuario_id or not livro_id or delta.days < 0:
                raise ValueError
            else:
                livro_emprestado = select(Livro).where(Livro.id_livro == livro_id)
                livro_emprestado = db_session.execute(livro_emprestado).scalar()
                if not livro_emprestado.status_emprestado:
                    post = Emprestimo(data_devolucao=data_devolucao,
                                      data_emprestimo=data_emprestimo,
                                      ID = usuario_id,
                                      ID_livro =livro_id
                                      )
                    post.save()
                    db_session.close()
                    livro_emprestado.status = True
                    return jsonify({'result': 'Emprestimo criado com sucesso!'}), 200
                else:
                    return jsonify(
                        {'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400

        else:
            raise ValueError
    except ValueError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400

@app.route('/livros', methods=['POST'])
def novo_livro():

    try:
        titulo = request.form['titulo']
        autor = request.form['autor']
        descricao = request.form['descricao']
        isbn = request.form['isbn']

        if not titulo or not autor or not isbn:
            raise ValueError
        else:
            post = Livro(titulo=titulo,
                         autor=autor,
                         descricao=descricao,
                         isbn=isbn,
                         status_emprestado=False)
            post.save()
            db_session.close()
            return jsonify({'result': 'Livro criado com sucesso!'}), 200

    except ValueError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400


@app.route('/usuarios/<id_user>', methods=['PUT'])
def editar_usuarios(id_user):
    try:
        id_usuario = id_user
        usuario_sql = select(Usuario).where(Usuario.id == id_usuario)
        usuario = db_session.execute(usuario_sql).scalar()
        json_dados_usuario = request.get_json()
        telefone = None
        cpf = None
        nome = None
        if 'telefone' in json_dados_usuario or 'cpf' in json_dados_usuario or 'nome' in json_dados_usuario:
            if 'telefone' in json_dados_usuario:
                telefone = json_dados_usuario['telefone']
            if 'cpf' in json_dados_usuario:
                cpf = json_dados_usuario['cpf']
            if 'nome' in json_dados_usuario:
                nome = json_dados_usuario['nome']

            if nome:
                nome = json_dados_usuario['nome']
                if not nome == '':
                    usuario.nome = nome
                else:
                    raise ValueError
            if cpf:
                cpf = json_dados_usuario['cpf']
                cpf = str(cpf)

                if not cpf == '':
                    if len(cpf) == 11:
                        cpf_f = '{0}.{1}.{2}-{3}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])
                        usuario.cpf = cpf_f
                    else:
                        raise ValueError
                else:
                    raise ValueError
            if telefone:
                tel = str(telefone)
                if not telefone == '':
                    if len(telefone) == 11:
                        tel_f = '{} {}-{}'.format(tel[:2], tel[2:7], tel[7:])
                        usuario.telefone = tel_f
                    else:
                        raise ValueError
                else:
                    raise ValueError

            usuario.save()
            return jsonify({'result': 'Usuario editado com sucesso!'}), 200

        else:
            raise ValueError

    except ValueError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400
    except sqlalchemy.exc.IntegrityError:
        return jsonify({'result': 'Error. Integrity Error (Erro de integridade) '}), 400


@app.route('/livros/<id_livro>', methods=['POST'])
def editar_livros(id_livro):
    id_livro = id_livro
    livro_sql = select(Livro).where(Livro.id_livro == id_livro)
    livro = db_session.execute(livro_sql).scalar()

    isbn = request.form['isbn']
    titulo = request.form['titulo']
    autor = request.form['autor']
    # status_emprestado = request.form['autor']
    descricao = request.form['descricao']

    if not isbn or not titulo or not autor:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400
    else:
        livro.isbn = isbn
        livro.titulo = titulo
        livro.autor = autor
        livro.descricao = descricao
        livro.save()
        return jsonify({'result': 'Livro editado com sucesso!'}), 200

@app.route('/emprestimos/<id_emp>', methods=['POST'])
def editar_emprestimos(id_emp):
    id_emprestimo = id_emp
    emprestimo_sql = select(Emprestimo, Usuario, Livro).join(
        Usuario, Emprestimo.ID == Usuario.id).join(
        Livro, Emprestimo.ID_livro == Livro.id_livro).where(
        Emprestimo.id_emprestimo == id_emprestimo)
    emprestimo = db_session.execute(emprestimo_sql).scalar()



if __name__ == '__main__':
    app.run(debug=True)