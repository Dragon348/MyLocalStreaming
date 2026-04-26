"""Initial migration - create all tables."""

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all database tables."""
    
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("cache_limit_mb", sa.Integer(), nullable=False, default=1024),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    
    # Artists table
    op.create_table(
        "artists",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artists_name"), "artists", ["name"], unique=True)
    
    # Albums table
    op.create_table(
        "albums",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("artist_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("cover_art_path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_albums_title"), "albums", ["title"], unique=False)
    
    # Tracks table
    op.create_table(
        "tracks",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("file_path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("bitrate_kbps", sa.Integer(), nullable=False),
        sa.Column("sample_rate_hz", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
        sa.Column("search_vector", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("album_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("artist_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("play_count", sa.Integer(), nullable=False, default=0),
        sa.Column("last_played", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"], ),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tracks_title"), "tracks", ["title"], unique=False)
    op.create_index(op.f("uq_tracks_file_path"), "tracks", ["file_path"], unique=True)
    op.create_index(op.f("ix_tracks_search_vector"), "tracks", ["search_vector"], unique=False)
    
    # Playlists table
    op.create_table(
        "playlists",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("owner_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Playlist tracks (many-to-many)
    op.create_table(
        "playlist_tracks",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("playlist_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("track_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], ),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_playlist_tracks_playlist_id"), "playlist_tracks", ["playlist_id"], unique=False)
    op.create_index(op.f("ix_playlist_tracks_track_id"), "playlist_tracks", ["track_id"], unique=False)
    
    # Sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("refresh_token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("device_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_sessions_refresh_token_hash"), "sessions", ["refresh_token_hash"], unique=False)


def downgrade() -> None:
    """Drop all database tables."""
    op.drop_table("sessions")
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
    op.drop_table("tracks")
    op.drop_table("albums")
    op.drop_table("artists")
    op.drop_table("users")
