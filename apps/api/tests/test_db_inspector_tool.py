from sqlalchemy.orm import Session
from app.tools.db_inspector import DbInspectorTool

def test_db_inspector_list_tables(db_session: Session) -> None:
    tool = DbInspectorTool(session=db_session)
    res = tool.run({"action": "list_tables"})
    assert "user" in res.lower()
    assert "conversations" in res.lower()
    assert "messages" in res.lower()

def test_db_inspector_inspect_nonexistent_table(db_session: Session) -> None:
    tool = DbInspectorTool(session=db_session)
    res = tool.run({"action": "inspect_table", "table_name": "nonexistent_table_xyz"})
    assert "does not exist" in res.lower() or "error" in res.lower()

def test_db_inspector_explain_non_select(db_session: Session) -> None:
    tool = DbInspectorTool(session=db_session)
    res = tool.run({"action": "explain_query", "query": "INSERT INTO user (id) VALUES ('abc')"})
    assert "only select queries are permitted" in res.lower()
    
    res_drop = tool.run({"action": "explain_query", "query": "DROP TABLE user"})
    assert "only select queries are permitted" in res_drop.lower()
