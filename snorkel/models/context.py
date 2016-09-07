from .meta import SnorkelBase, snorkel_postgres
from sqlalchemy import Column, String, Integer, Table, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import PickleType
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql import select, text
import pandas as pd


corpus_document_association = Table('corpus_document_association', SnorkelBase.metadata,
                                    Column('corpus_id', Integer, ForeignKey('corpus.id')),
                                    Column('document_id', Integer, ForeignKey('document.id')))


class Corpus(SnorkelBase):
    """
    A set of Documents, uniquely identified by a name.

    Corpora have many-to-many relationships with Documents, so users can create new
    subsets, supersets, etc.
    """
    __tablename__ = 'corpus'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    documents = relationship('Document', secondary=corpus_document_association, backref='corpora')
    # TODO: What should the cascades be?

    def append(self, item):
        self.documents.append(item)

    def remove(self, item):
        self.documents.remove(item)

    def __repr__(self):
        return "Corpus (" + str(self.name) + ")"

    def __iter__(self):
        """Default iterator is over self.documents"""
        for doc in self.documents:
            yield doc

    def __len__(self):
        return len(self.documents)

    def stats(self):
        """Print summary / diagnostic stats about the corpus"""
        print "Number of documents:", len(self.documents)
        self.child_context_stats(Document)

    def child_context_stats(self, parent_context):
        """
        Given a parent context class, gets all the child context classes, and returns histograms of the number
        of children per parent.
        """
        session = object_session(self)
        parent_name = parent_context.__table__.name

        # Get all the child context relationships
        rels = [r for r in inspect(parent_context).relationships if r.back_populates == parent_name]
        
        # Print the histograms for each child context, and recurse!
        for rel in rels:
            c  = rel.mapper.class_
            fk = list(rel._calculated_foreign_keys)[0]
                
            # Query for average number of child contexts per parent context
            label = 'Number of %ss per %s' % (c.__table__.name, parent_name)
            query = session.query(fk, func.count(c.id).label(label)).group_by(fk) 
                
            # Render as panadas dataframe histogram
            df = pd.read_sql(query.statement, query.session.bind)
            df.hist(label)

            # Recurse to grandhildren
            self.child_context_stats(c)


class Context(SnorkelBase):
    """
    A piece of content from which Candidates are composed.
    """
    __tablename__ = 'context'
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    stable_id = Column(String, unique=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'context',
        'polymorphic_on': type
    }


class Document(Context):
    """
    A root Context.
    """
    __tablename__ = 'document'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    meta = Column(PickleType)

    __mapper_args__ = {
        'polymorphic_identity': 'document',
    }

    def __repr__(self):
        return "Document " + str(self.name)


class Sentence(Context):
    """A sentence Context in a Document."""
    __tablename__ = 'sentence'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    document = relationship('Document', backref=backref('sentences', cascade='all, delete-orphan'), foreign_keys=document_id)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    if snorkel_postgres:
        words = Column(postgresql.ARRAY(String), nullable=False)
        char_offsets = Column(postgresql.ARRAY(Integer), nullable=False)
        lemmas = Column(postgresql.ARRAY(String))
        poses = Column(postgresql.ARRAY(String))
        dep_parents = Column(postgresql.ARRAY(Integer))
        dep_labels = Column(postgresql.ARRAY(String))
    else:
        words = Column(PickleType, nullable=False)
        char_offsets = Column(PickleType, nullable=False)
        lemmas = Column(PickleType)
        poses = Column(PickleType)
        dep_parents = Column(PickleType)
        dep_labels = Column(PickleType)

    __mapper_args__ = {
        'polymorphic_identity': 'sentence',
    }

    __table_args__ = (
        UniqueConstraint(document_id, position),
    )

    def _asdict(self):
        return {
            'id': self.id,
            'document': self.document,
            'position': self.position,
            'text': self.text,
            'words': self.words,
            'char_offsets': self.char_offsets,
            'lemmas': self.lemmas,
            'poses': self.poses,
            'dep_parents': self.dep_parents,
            'dep_labels': self.dep_labels
        }

    def __repr__(self):
        return "Sentence" + str((self.document, self.position, self.text))


class Table(Context):
    """A table Context in a Document."""
    __tablename__ = 'table'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    document = relationship('Document', backref=backref('tables', cascade='all, delete-orphan'), foreign_keys=document_id)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'table',
    }

    __table_args__ = (
        UniqueConstraint(document_id, position),
    )

    def __repr__(self):
        return "Table" + str((self.document, self.position, self.text))


class Cell(Context):
    """A cell Context in a Document."""
    __tablename__ = 'cell'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    table_id = Column(Integer, ForeignKey('table.id'))
    document = relationship('Document', backref=backref('cells', cascade='all, delete-orphan'), foreign_keys=document_id)
    table = relationship('Table', backref=backref('cells', cascade='all, delete-orphan'), foreign_keys=table_id)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    row_num = Column(Integer)
    col_num = Column(Integer)
    html_tag = Column(Text)
    if snorkel_postgres:
        html_attrs = Column(postgresql.ARRAY(String))
        html_anc_tags = Column(postgresql.ARRAY(String))
        html_anc_attrs = Column(postgresql.ARRAY(String))
    else:
        html_attrs = Column(PickleType)
        html_anc_tags = Column(PickleType)
        html_anc_attrs = Column(PickleType)

    __mapper_args__ = {
        'polymorphic_identity': 'cell',
    }

    __table_args__ = (
        UniqueConstraint(document_id, table_id, position),
    )

    def __repr__(self):
        return "Cell" + str((self.document, self.table, self.position, self.text))


class Phrase(Context):
    """A phrase Context in a Document."""
    __tablename__ = 'phrase'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    document_id = Column(Integer, ForeignKey('document.id'))
    table_id = Column(Integer, ForeignKey('table.id'))
    cell_id = Column(Integer, ForeignKey('cell.id'))
    document = relationship('Document', backref=backref('phrases', cascade='all, delete-orphan'), foreign_keys=document_id)
    table = relationship('Table', backref=backref('phrases', cascade='all, delete-orphan'), foreign_keys=table_id)
    cell = relationship('Cell', backref=backref('phrases', cascade='all, delete-orphan'), foreign_keys=cell_id)
    position = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    # table_num = Column(Integer)
    # cell_num = Column(Integer)
    row_num = Column(Integer)
    col_num = Column(Integer)
    html_tag = Column(Text)
    if snorkel_postgres:
        html_attrs = Column(postgresql.ARRAY(String))
        html_anc_tags = Column(postgresql.ARRAY(String))
        html_anc_attrs = Column(postgresql.ARRAY(String))
        words = Column(postgresql.ARRAY(String), nullable=False)
        char_offsets = Column(postgresql.ARRAY(Integer), nullable=False)
        lemmas = Column(postgresql.ARRAY(String))
        poses = Column(postgresql.ARRAY(String))
        dep_parents = Column(postgresql.ARRAY(Integer))
        dep_labels = Column(postgresql.ARRAY(String))
    else:
        html_attrs = Column(PickleType)
        html_anc_tags = Column(PickleType)
        html_anc_attrs = Column(PickleType)
        words = Column(PickleType, nullable=False)
        char_offsets = Column(PickleType, nullable=False)
        lemmas = Column(PickleType)
        poses = Column(PickleType)
        dep_parents = Column(PickleType)
        dep_labels = Column(PickleType)

    __mapper_args__ = {
        'polymorphic_identity': 'phrase',
    }

    __table_args__ = (
        UniqueConstraint(document_id, table_id, cell_id, position),
    )

    def _asdict(self):
        return {
            'id': self.id,
            'document': self.document,
            'position': self.position,
            'text': self.text,
            'table_num': self.table_num,
            'cell_num': self.cell_num,
            'row_num': self.row_num,
            'col_num': self.col_num,
            'html_tag': self.html_tag,
            'html_attrs': self.html_attrs,
            'html_anc_tags': self.html_anc_tags,
            'html_anc_attrs': self.html_anc_attrs,
            'words': self.words,
            'char_offsets': self.char_offsets,
            'lemmas': self.lemmas,
            'poses': self.poses,
            'dep_parents': self.dep_parents,
            'dep_labels': self.dep_labels
        }

    def __repr__(self):
        return "Phrase" + str((self.document, self.position, self.text))


class TemporaryContext(object):
    """
    A context which does not incur the overhead of a proper ORM-based Context object.
    The TemporaryContext class is specifically for the candidate extraction process, during which a CandidateSpace
    object will generate many TemporaryContexts, which will then be filtered by Matchers prior to materialization
    of Candidates and constituent Context objects.

    Every Context object has a corresponding TemporaryContext object from which it inherits.

    A TemporaryContext must have specified equality / set membership semantics, a stable_id for checking
    uniqueness against the database, and a promote() method which returns a corresponding Context object.
    """
    def __init__(self):
        self.id = None

    def load_id_or_insert(self, session):
        if self.id is None:
            stable_id = self.get_stable_id()
            id = session.execute(select([Context.id]).where(Context.stable_id == stable_id)).first()
            if id is None:
                self.id = session.execute(
                        Context.__table__.insert(),
                        {'type': self._get_table_name(), 'stable_id': stable_id}).inserted_primary_key[0]
                insert_args = self._get_insert_args()
                insert_args['id'] = self.id
                session.execute(text(self._get_insert_query()), insert_args)
            else:
                self.id = id[0]

    def __eq__(self, other):
        raise NotImplementedError()

    def __ne__(self, other):
        raise NotImplementedError()

    def __hash__(self):
        raise NotImplementedError()

    def _get_polymorphic_identity(self):
        raise NotImplementedError()

    def get_stable_id(self):
        raise NotImplementedError()

    def _get_table_name(self):
        raise NotImplementedError()

    def _get_insert_query(self):
        raise NotImplementedError()

    def _get_insert_args(self):
        raise NotImplementedError()


class TemporarySpan(TemporaryContext):
    """The TemporaryContext version of Span"""
    def __init__(self, parent, char_start, char_end, meta=None):
        super(TemporarySpan, self).__init__()
        self.parent     = parent  # The parent Context of the Span
        self.char_end   = char_end
        self.char_start = char_start
        self.meta       = meta

    def __len__(self):
        return self.char_end - self.char_start + 1

    def __eq__(self, other):
        try:
            return self.parent == other.parent and self.char_start == other.char_start \
                and self.char_end == other.char_end
        except AttributeError:
            return False

    def __ne__(self, other):
        try:
            return self.parent != other.parent or self.char_start != other.char_start \
                or self.char_end != other.char_end
        except AttributeError:
            return True

    def __hash__(self):
        return hash(self.parent) + hash(self.char_start) + hash(self.char_end)

    def get_stable_id(self):
        return construct_stable_id(self.parent, self._get_polymorphic_identity(), self.char_start, self.char_end)

    def _get_table_name(self):
        return 'span'

    def _get_polymorphic_identity(self):
        return 'span'

    def _get_insert_query(self):
        return """INSERT INTO span VALUES(:id, :parent_id, :char_start, :char_end, :meta)"""

    def _get_insert_args(self):
        return {'parent_id' : self.parent.id,
                'char_start': self.char_start,
                'char_end'  : self.char_end,
                'meta'      : self.meta}

    def get_word_start(self):
        return self.char_to_word_index(self.char_start)

    def get_word_end(self):
        return self.char_to_word_index(self.char_end)

    def get_n(self):
        return self.get_word_end() - self.get_word_start() + 1

    def char_to_word_index(self, ci):
        """Given a character-level index (offset), return the index of the **word this char is in**"""
        i = None
        for i, co in enumerate(self.parent.char_offsets):
            if ci == co:
                return i
            elif ci < co:
                return i-1
        return i

    def word_to_char_index(self, wi):
        """Given a word-level index, return the character-level index (offset) of the word's start"""
        return self.parent.char_offsets[wi]

    def get_attrib_tokens(self, a='words'):
        """Get the tokens of sentence attribute _a_ over the range defined by word_offset, n"""
        return self.parent.__getattribute__(a)[self.get_word_start():self.get_word_end() + 1]

    def get_attrib_span(self, a, sep=" "):
        """Get the span of sentence attribute _a_ over the range defined by word_offset, n"""
        # NOTE: Special behavior for words currently (due to correspondence with char_offsets)
        if a == 'words':
            return self.parent.text[self.char_start:self.char_end + 1]
        else:
            return sep.join(self.get_attrib_tokens(a))

    def get_span(self, sep=" "):
        return self.get_attrib_span('words', sep)

    def __contains__(self, other_span):
        return other_span.char_start >= self.char_start and other_span.char_end <= self.char_end

    def __getitem__(self, key):
        """
        Slice operation returns a new candidate sliced according to **char index**
        Note that the slicing is w.r.t. the candidate range (not the abs. sentence char indexing)
        """
        if isinstance(key, slice):
            char_start = self.char_start if key.start is None else self.char_start + key.start
            if key.stop is None:
                char_end = self.char_end
            elif key.stop >= 0:
                char_end = self.char_start + key.stop - 1
            else:
                char_end = self.char_end + key.stop
            return self._get_instance(char_start=char_start, char_end=char_end, parent=self.parent)
        else:
            raise NotImplementedError()

    def __repr__(self):
        return '%s("%s", parent=%s, chars=[%s,%s], words=[%s,%s])' \
            % (self.__class__.__name__, self.get_span(), self.parent.id, self.char_start, self.char_end,
               self.get_word_start(), self.get_word_end())

    def _get_instance(self, **kwargs):
        return TemporarySpan(**kwargs)


class Span(Context, TemporarySpan):
    """
    A span of characters, identified by Context id and character-index start, end (inclusive).

    char_offsets are **relative to the Context start**
    """
    __tablename__ = 'span'
    id = Column(Integer, ForeignKey('context.id'), primary_key=True)
    parent_id = Column(Integer, ForeignKey('context.id'))
    char_start = Column(Integer, nullable=False)
    char_end = Column(Integer, nullable=False)
    meta = Column(PickleType)

    __table_args__ = (
        UniqueConstraint(parent_id, char_start, char_end),
    )

    __mapper_args__ = {
        'polymorphic_identity': 'span',
        'inherit_condition': (id == Context.id)
    }

    parent = relationship('Context', backref=backref('spans', cascade='all, delete-orphan'), foreign_keys=parent_id)

    def _get_instance(self, **kwargs):
        return Span(**kwargs)

    # We redefine these to use default semantics, overriding the operators inherited from TemporarySpan
    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __hash__(self):
        return id(self)


def split_stable_id(stable_id):
    """
    Split stable id, returning:
        * Parent (root) stable ID
        * Context polymorphic type
        * Character offset start, end *relative to parent start*
    Returns tuple of four values.
    """
    split1 = stable_id.split('::')
    if len(split1) == 2:
        split2 = split1[1].split(':')
        if len(split2) == 3:
            return split1[0], split2[0], int(split2[1]), int(split2[2])
    raise ValueError("Malformed stable_id:", stable_id)


def construct_stable_id(parent_context, polymorphic_type, relative_char_offset_start, relative_char_offset_end):
    """Contruct a stable ID for a Context given its parent and its character offsets relative to the parent"""
    parent_id, _, parent_char_start, _ = split_stable_id(parent_context.stable_id)
    start = parent_char_start + relative_char_offset_start
    end   = parent_char_start + relative_char_offset_end
    return "%s::%s:%s:%s" % (parent_id, polymorphic_type, start, end)