from sqlalchemy import text
from sqlalchemy.engine import Connection


def install_notes_fts(conn: Connection, cfg: str = "simple"):
    # 1) Create or replace the trigger function (no DO block here)
    conn.execute(
        text(
            f"""
CREATE OR REPLACE FUNCTION notes_tsv_trigger() RETURNS trigger AS $fn$
BEGIN
    IF NEW.title = 'Ghi chú hình ảnh' THEN
        IF NEW.content IS NULL OR NEW.content = '' THEN
            NEW.content_tsv := to_tsvector('{cfg}', '');
        ELSE
            NEW.content_tsv := to_tsvector('{cfg}', NEW.content);
        END IF;
    ELSE
        NEW.content_tsv := to_tsvector('{cfg}', coalesce(NEW.title,'') || ' ' || coalesce(NEW.content,''));
    END IF;
    RETURN NEW;
END
$fn$ LANGUAGE plpgsql;
"""
        )
    )

    # 2) Create the trigger only if not exists via a DO block
    conn.execute(
        text(
            """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'notes_content_tsv_trigger'
    ) THEN
        CREATE TRIGGER notes_content_tsv_trigger BEFORE INSERT OR UPDATE OF title, content
        ON notes FOR EACH ROW EXECUTE FUNCTION notes_tsv_trigger();
    END IF;
END$$;
"""
        )
    )


def install_ocr_fts(conn: Connection, cfg: str = "simple"):
    # 1) Create or replace the trigger function
    conn.execute(
        text(
            f"""
CREATE OR REPLACE FUNCTION ocr_texts_tsv_trigger() RETURNS trigger AS $fn$
BEGIN
    NEW.text_tsv := to_tsvector('{cfg}', coalesce(NEW.text,''));
    RETURN NEW;
END
$fn$ LANGUAGE plpgsql;
"""
        )
    )

    conn.execute(
        text(
            """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'ocr_texts_tsv_trigger'
    ) THEN
        CREATE TRIGGER ocr_texts_tsv_trigger BEFORE INSERT OR UPDATE OF text
        ON ocr_texts FOR EACH ROW EXECUTE FUNCTION ocr_texts_tsv_trigger();
    END IF;
END$$;
"""
        )
    )