"""
Thiết lập tìm kiếm toàn văn cho PostgreSQL trên bảng note_items.
"""
from sqlalchemy import text
from sqlalchemy.engine import Connection


def install_note_items_fts(conn: Connection, cfg: str = "simple"):
    """
    Cài đặt trigger tìm kiếm toàn văn cho bảng note_items.
    
    Args:
        conn: Kết nối cơ sở dữ liệu
        cfg: Cấu hình tìm kiếm văn bản PostgreSQL (mặc định: "simple")
    """
    # Tạo hoặc thay thế hàm trigger
    conn.execute(
        text(
            f"""
CREATE OR REPLACE FUNCTION note_items_tsv_trigger() RETURNS trigger AS $fn$
BEGIN
    -- Kết hợp title + content_text + ocr_text + image_metadata thành tsvector
    NEW.tsv_content := to_tsvector(
        '{cfg}',
        coalesce(NEW.title,'') || ' ' ||
        coalesce(NEW.content_text,'') || ' ' ||
        coalesce(NEW.ocr_text,'') || ' ' ||
        coalesce(NEW.image_metadata::text,'')
    );
    RETURN NEW;
END
$fn$ LANGUAGE plpgsql;
"""
        )
    )

    # Tạo trigger chỉ khi chưa tồn tại
    conn.execute(
        text(
            """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'note_items_tsv_content_trigger'
    ) THEN
        CREATE TRIGGER note_items_tsv_content_trigger
        BEFORE INSERT OR UPDATE OF title, content_text, ocr_text, image_metadata
        ON note_items
        FOR EACH ROW EXECUTE FUNCTION note_items_tsv_trigger();
    END IF;
END$$;
"""
        )
    )
    
    # Tạo GIN index cho tsvector nếu chưa có
    conn.execute(
        text(
            """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_note_items_tsv_content'
    ) THEN
        CREATE INDEX idx_note_items_tsv_content 
        ON note_items USING GIN(tsv_content);
    END IF;
END$$;
"""
        )
    )
