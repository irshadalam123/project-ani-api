"""Repository interfaces and implementations.

* ``app.repositories.interfaces``  – ABCs (persistence ports) used by services.
* ``app.repositories.memory``      – Process-local in-memory stores (default).
* ``app.repositories.postgres``    – SQLAlchemy async implementations backed by
                                     PostgreSQL.  Selected in
                                     ``app.core.container.build_container`` when
                                     ``DATABASE_URL`` is configured.  Routes,
                                     services, workers, and the automation
                                     engine are unaffected by the swap.
"""
