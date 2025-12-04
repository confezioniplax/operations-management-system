class SqlUserAuth:
    @staticmethod
    def get_user_info_auth():
        return """
            SELECT
                o.id                  AS employee_id,
                o.email               AS email,
                o.first_name          AS first_name,
                o.last_name           AS last_name,
                NULL                  AS hire_date,
                NULL                  AS end_date,
                o.user_password       AS user_password,
                COALESCE(o.role,'HR') AS role
            FROM operators o
            WHERE o.email = %s
            LIMIT 1
        """
