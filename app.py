from flask import Flask, jsonify, redirect, request
from flask_pydantic_spec import FlaskPydanticSpec
from datetime import date
from dateutil.relativedelta import relativedelta
from models import local_session, Livro, Emprestimo, Usuario
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
    """
        API para gerenciar uma biblioteca integrada a um banco de dados

    """
    return redirect('/livros')
@app.route('/livros', methods=['GET'])
@app.route('/livros/<status>', methods=['GET'])
def get_livros(status=None):
    """
        Consultar livros

        ### Endpoint:
            GET /livros
            GET /livros/<status>

        ### Parâmetros:
        - `status` **(str)**: **string para ser convertida a boolean**

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** com a lista de livros e dados
        - **JSON** com a lista de livros e dados que possuam o `status` igual ao recebido de parâmetro
    """

    try:
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
    except IntegrityError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400


@app.route('/usuarios', methods=['GET'])
@app.route('/usuarios/<id_user>', methods=['GET'])
def get_usuarios(id_user=None):
    """
        Consultar usuários

        ### Endpoint:
            GET /usuarios
            GET /usuarios/<id_user>

        ### Parâmetros:
        - `id_user` **(str)**: **string para ser convertida a inteiro**

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** com a lista de usuários e dados
    """
    try:
        sql = select(Usuario)
        sql_executar = db_session.execute(sql).scalars()
        result = []
        for usuario in sql_executar:
            result.append(usuario.serialize_usuario())
        return jsonify({'result': result})
    except ValueError:
        return jsonify({'result': 'Error. Erro de Valor'})


@app.route('/emprestimos/<id_user>', methods=['GET'])
def get_emprestimos_user(id_user):
    """
            Consultar emprestimos por usuario

            ### Endpoint:
                GET /emprestimos/<id_user>

            ### Parâmetros:
            - `id_user` **(str)**: **string para ser convertida a inteiro**

            ### Erros possíveis:
            - **Bad Request**: *status code* **400**

            ### Retorna:
            - **JSON** com a lista de emprestimos realizados pelo usuario
        """

    try:
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
    """
        Consultar emprestimos

        ### Endpoint:
            GET /emprestimos

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** com a lista de emprestimos
    """

    try:
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
    except IntegrityError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400


@app.route('/usuarios', methods=['POST'])
def novo_usuario():
    """
        Cadastrar usuario

        ### Endpoint:
            POST /usuarios

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """
    db_session = local_session()
    try:
        dados_usuario = request.get_json()
        nome = dados_usuario['nome']
        cpf = dados_usuario['cpf']
        telefone = dados_usuario['telefone']
        cpf = str(cpf)
        if not nome or not cpf or not telefone or len(cpf) != 11:
            return jsonify({'result': 'Error. Integrity Error (faltam informações) '}), 400
        else:
            cpf_f = '{0}.{1}.{2}-{3}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])
            usuario = select(Usuario).where(Usuario.cpf == cpf_f)
            usuario = db_session.execute(usuario).scalars()
            if usuario:
                raise TypeError
            else:
                post = Usuario(nome=nome, cpf=cpf_f, telefone=telefone)
                post.save(db_session)
                db_session.close()
                return jsonify({'result': 'Usuario criado com sucesso!'}), 200
    except TypeError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route('/emprestimos', methods=['POST'])
def novo_emprestimo():
    """
        Cadastrar emprestimos

        ### Endpoint:
            POST /emprestimos

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """

    json_dados_emprestimo = request.get_json()
    data_emprestimo = json_dados_emprestimo['data_emprestimo']
    usuario_id = json_dados_emprestimo['id_usuario']
    livro_id = json_dados_emprestimo['id_livro']

    tempo_emprestimo = json_dados_emprestimo['tempo_emprestimo']
    tipo_tempo = json_dados_emprestimo['tipo_tempo']
    try:
        if len(data_emprestimo) == 10:
            usuario_id = int(usuario_id)
            livro_id = int(livro_id)
            # data formato yyyy-mm-dd
            ano_emprestimo = '{}'.format(data_emprestimo[:4])
            mes_emprestimo = '{}'.format(data_emprestimo[5:7])
            dia_emprestimo = '{}'.format(data_emprestimo[8:])

            obj_data_emprestimo = date(int(ano_emprestimo), int(mes_emprestimo), int(dia_emprestimo))

            tipos_validos = ['d', 'w', 'm', 'y']
            if tipo_tempo in tipos_validos:
                data_devolucao = None
                if tipo_tempo == 'd':
                    data_devolucao = data_emprestimo + relativedelta(days=tempo_emprestimo)

                elif tipo_tempo == 'w':
                    data_devolucao = data_emprestimo + relativedelta(weeks=tempo_emprestimo)

                elif tipo_tempo == 'm':
                    data_devolucao = data_emprestimo + relativedelta(months=tempo_emprestimo)

                elif tipo_tempo == 'y':
                    data_devolucao = data_emprestimo + relativedelta(years=tempo_emprestimo)

                # ano_devolucao = '{}'.format(data_devolucao[:4])
                # mes_devolucao = '{}'.format(data_devolucao[5:7])
                # dia_devolucao = '{}'.format(data_devolucao[8:])

                # obj_data_devolucao = date(int(ano_devolucao), int(mes_devolucao), int(dia_devolucao))

                delta = data_devolucao - obj_data_emprestimo
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
        else:
            raise ValueError
    except ValueError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400

@app.route('/livros', methods=['POST'])
def novo_livro():
    """
        Cadastrar livros

        ### Endpoint:
            POST /livros

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """
    try:
        json_dados_livro = request.get_json()
        titulo = json_dados_livro['titulo']
        autor = json_dados_livro['autor']
        descricao = json_dados_livro['descricao']
        isbn = json_dados_livro['isbn']

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
    """
        Editar usuarios

        ### Endpoint:
            PUT /usuarios/<id_user>

        ### Parâmetros:
        - `id_user` **(str)**: **string para ser convertida a inteiro**

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """

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
                        select_usuario = select(Usuario).where(Usuario.cpf == cpf_f)
                        sql_usuario = db_session.execute(select_usuario).scalars()
                        if sql_usuario:
                            print('cpf igaullllll')
                            raise ValueError
                        else:
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


@app.route('/livros/<id_livro>', methods=['PUT'])
def editar_livros(id_livro):
    """
        Editar livros

        ### Endpoint:
            PUT /livros/<id_livro>

        ### Parâmetros:
        - `id_livro` **(str)**: **string para ser convertida a inteiro**

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """

    try:
        id_livro = id_livro
        livro_sql = select(Livro).where(Livro.id_livro == id_livro)
        livro = db_session.execute(livro_sql).scalar()
        json_dados_livro = request.get_json()
        # status_emprestado = request.form['autor']
        isbn = None
        descricao = None
        autor = None
        titulo = None
        if 'isbn' in json_dados_livro or 'titulo' in json_dados_livro or 'autor' in json_dados_livro or 'descricao' in json_dados_livro:
            if 'isbn' in json_dados_livro:
                isbn = json_dados_livro['isbn']
            if 'titulo' in json_dados_livro:
                titulo = json_dados_livro['titulo']
            if 'autor' in json_dados_livro:
                autor = json_dados_livro['autor']
            if 'descricao' in json_dados_livro:
                descricao = json_dados_livro['descricao']

            if titulo:
                if titulo == '':
                    raise TypeError
                else:
                    livro.titulo = titulo

            if autor:
                if autor == '':
                    raise TypeError
                else:
                    livro.autor = autor

            if descricao:
                livro.descricao = descricao

            if isbn:
                if isbn == '':
                    raise TypeError
                else:
                    int(isbn)
                    livro.isbn = isbn

            livro.save()
            return jsonify({'result': 'Livro editado com sucesso!'}), 200

        else:
            raise TypeError
    except TypeError:
        return jsonify({'result': 'Error. TypeError (faltam informações ou informações corretas) '}), 400
    except ValueError:
        return jsonify({'result': 'Error. ValueError (faltam informações ou informações corretas) '}), 400


@app.route('/emprestimos/<id_emp>', methods=['PUT'])
def editar_emprestimos(id_emp):
    """
        Editar emprestimos

        ### Endpoint:
            PUT /emprestimos/<id_emp>

        ### Parâmetros:
        - `id_emp` **(str)**: **string para ser convertida a inteiro**

        ### Erros possíveis:
        - **Bad Request**: *status code* **400**

        ### Retorna:
        - **JSON** mensagem de **sucesso**
    """

    try:
        id_emprestimo = id_emp
        emprestimo_sql = select(Emprestimo, Usuario, Livro).join(
            Usuario, Emprestimo.ID == Usuario.id).join(
            Livro, Emprestimo.ID_livro == Livro.id_livro).where(
            Emprestimo.id_emprestimo == id_emprestimo)
        emprestimo = db_session.execute(emprestimo_sql).scalar()

        json_dados_emprestimo = request.get_json()

        if 'status' in json_dados_emprestimo:
            status = json_dados_emprestimo['status']
            if not status == '':
                if status in ['True', 1, '1']:
                    status = True
                elif status in ['False', 0, '0']:
                    status = False
                else:
                    raise ValueError
                emprestimo.status_finalizado = status
                emprestimo.save()
                return jsonify({'result': 'Emprestimo editado com sucesso!'}), 200

            else:
                raise ValueError
        else:
            raise TypeError

    except TypeError:
        return jsonify({'result': 'Error. Integrity Error (faltam informações ou informações corretas) '}), 400




if __name__ == '__main__':
    app.run(debug=True)