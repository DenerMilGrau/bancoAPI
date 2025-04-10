#importar biblioteca.
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean, Date

#importar session e sessionmaker.
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base, relationship, Relationship

#configurar a conexão de banco.
engine = create_engine('sqlite:///base_biblioteca.sqlite3')

#gerenciar sessao com banco de dados.
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class Usuario(Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    cpf = Column(String, nullable=False, unique=True)
    telefone = Column(String, nullable=False)

    def __repr__(self):
        return '<Usuario(id={}, nome={})>'.format(self.id, self.nome)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_usuario(self):
        dados_usuario = {
            'id': self.id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
        }
        return dados_usuario

class Livro(Base):
    __tablename__ = 'livro'
    id_livro = Column(Integer, primary_key=True)
    isbn = Column(String, nullable=False)
    titulo = Column(String, nullable=False, index=True)
    autor = Column(String, nullable=False, index=True)
    status_emprestado = Column(Boolean, nullable=False, index=True, default=False)
    descricao = Column(String)

    def __repr__(self):
        return 'id_livro={}, titulo={}'.format(self.id_livro, self.titulo)

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_livro(self):
        dados_livro = {
            'id_livro': self.id_livro,
            'isbn': self.isbn,
            'titulo': self.titulo,
            'autor': self.autor,
            'descricao': self.descricao,
            'status_emprestado': self.status_emprestado,
        }
        return dados_livro

class Emprestimo(Base):
    __tablename__ = 'emprestimo'
    id_emprestimo = Column(Integer, primary_key=True)
    data_emprestimo = Column(String, nullable=False)
    data_devolucao = Column(String, nullable=False)
    status_finalizado = Column(Boolean, nullable=False, default=False)

    ID = Column(Integer, ForeignKey('usuario.id'))
    ID_livro = Column(Integer, ForeignKey('livro.id_livro'))
    usuario_relacao = Relationship('Usuario')
    livro_relacao = Relationship('Livro')

    def __repr__(self):
        return '<id_emprestimo={}, id_livro={}, id_usuario={}>'.format(self.id_emprestimo,
                                                                       self.ID_livro,
                                                                       self.ID)
    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize_emprestimo(self):
        dados_emprestimo = {
            'id_emprestimo': self.id_emprestimo,
            'data_emprestimo': self.data_emprestimo,
            'data_devolucao': self.data_devolucao,
            'status_finalizado': self.status_finalizado,
            'ID': self.ID,
            'ID_livro': self.ID_livro,
        }
        return dados_emprestimo

def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    init_db()