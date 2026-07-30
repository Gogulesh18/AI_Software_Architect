from app.analyzer.database import detect_database
from app.parser.extractor import parse_source


def test_sqlalchemy_model_detected():
    src = '''
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    org_id = Column(Integer, ForeignKey("organizations.id"))
'''
    pf = parse_source("models/user.py", "python", src)
    result = detect_database([pf])

    assert "sqlalchemy" in result["orms_detected"]
    table = result["tables"][0]
    assert table["name"] == "users"
    col_names = {c["name"] for c in table["columns"]}
    assert col_names == {"id", "name", "org_id"}
    id_col = next(c for c in table["columns"] if c["name"] == "id")
    assert id_col["primary_key"] is True
    org_col = next(c for c in table["columns"] if c["name"] == "org_id")
    assert org_col["foreign_key"] == "organizations.id"


def test_django_model_detected():
    src = '''
class Article(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
'''
    pf = parse_source("app/models.py", "python", src)
    result = detect_database([pf])

    assert "django" in result["orms_detected"]
    table = result["tables"][0]
    assert table["name"] == "Article"
    names = {c["name"] for c in table["columns"]}
    assert {"id", "title", "author"} <= names
    author_col = next(c for c in table["columns"] if c["name"] == "author")
    assert author_col["foreign_key"] == "Author"


def test_typeorm_entity_detected():
    src = """
@Entity()
class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  email: string;

  @ManyToOne(() => Organization)
  organization: Organization;
}
"""
    pf = parse_source("user.ts", "typescript", src)
    result = detect_database([pf])

    assert "typeorm" in result["orms_detected"]
    table = result["tables"][0]
    id_col = next(c for c in table["columns"] if c["name"] == "id")
    assert id_col["primary_key"] is True
    org_col = next(c for c in table["columns"] if c["name"] == "organization")
    assert org_col["foreign_key"] == "Organization"


def test_jpa_entity_detected():
    src = """
@Entity
public class User {
    @Id
    private Long id;

    @Column
    private String email;
}
"""
    pf = parse_source("User.java", "java", src)
    result = detect_database([pf])

    assert "hibernate/jpa" in result["orms_detected"]
    table = result["tables"][0]
    id_col = next(c for c in table["columns"] if c["name"] == "id")
    assert id_col["primary_key"] is True


def test_prisma_schema_detected():
    src = """
model User {
  id    Int    @id @default(autoincrement())
  email String @unique
  posts Post[] @relation
}
"""
    pf = parse_source("schema.prisma", "text", src)
    pf.source = src  # shallow-parsed files still carry source
    result = detect_database([pf])

    assert "prisma" in result["orms_detected"]
    table = result["tables"][0]
    assert table["name"] == "User"
    id_col = next(c for c in table["columns"] if c["name"] == "id")
    assert id_col["primary_key"] is True


def test_no_orm_detected_returns_empty():
    pf = parse_source("main.py", "python", "x = 1\n")
    result = detect_database([pf])
    assert result["orms_detected"] == []
    assert result["tables"] == []
