from app.repositories.report_repository import ReportRepository


class ReportService:

    def __init__(self):
        self.repo = ReportRepository()

    def get_today_profit_summary(
        self,
        db,
        business_id,
    ):
        result = self.repo.get_today_summary(
            db,
            business_id,
        )

        revenue = float(result.revenue or 0)
        cogs = float(result.cogs or 0)
        profit = float(result.profit or 0)

        margin = 0

        if revenue > 0:
            margin = round((profit / revenue) * 100, 2)

        return {
            "transactions": result.transactions or 0,
            "revenue": revenue,
            "cost_of_goods_sold": cogs,
            "gross_profit": profit,
            "profit_margin": margin,
        }