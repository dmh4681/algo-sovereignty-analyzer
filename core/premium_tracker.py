"""
Physical Premium Tracker Module

Tracks premiums on physical gold and silver products across dealers.
Uses seeded data with manual update capability (no scraping).
"""

import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "premium_tracker.db"


@dataclass
class Dealer:
    """Represents a precious metals dealer."""
    id: str
    name: str
    website: str
    shipping_info: str
    min_free_shipping: Optional[float]
    is_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'shipping_info': self.shipping_info,
            'min_free_shipping': self.min_free_shipping,
            'is_active': self.is_active,
        }


@dataclass
class Product:
    """Represents a physical precious metals product."""
    id: str
    name: str
    metal: str  # 'gold' or 'silver'
    weight_oz: float
    product_type: str  # 'coin', 'bar', 'round', 'junk'
    mint: Optional[str]
    is_government: bool
    typical_premium_low: float  # Expected premium range
    typical_premium_high: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'metal': self.metal,
            'weight_oz': self.weight_oz,
            'product_type': self.product_type,
            'mint': self.mint,
            'is_government': self.is_government,
            'typical_premium_low': self.typical_premium_low,
            'typical_premium_high': self.typical_premium_high,
        }


@dataclass
class ProductPrice:
    """A specific product price at a specific dealer."""
    id: Optional[int]
    product_id: str
    dealer_id: str
    price: float
    quantity: int  # Price for this quantity (1, 10, 100)
    spot_price: float
    premium_dollars: float
    premium_percent: float
    in_stock: bool
    product_url: Optional[str]
    captured_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'product_id': self.product_id,
            'dealer_id': self.dealer_id,
            'price': self.price,
            'quantity': self.quantity,
            'spot_price': self.spot_price,
            'premium_dollars': self.premium_dollars,
            'premium_percent': self.premium_percent,
            'in_stock': self.in_stock,
            'product_url': self.product_url,
            'captured_at': self.captured_at,
        }


@dataclass
class DealerComparison:
    """Product comparison across dealers."""
    product: Product
    prices: List[Dict[str, Any]]  # Includes dealer info
    best_price: Optional[Dict[str, Any]]
    spot_price: float
    melt_value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'product': self.product.to_dict(),
            'prices': self.prices,
            'best_price': self.best_price,
            'spot_price': self.spot_price,
            'melt_value': self.melt_value,
        }


@dataclass
class DealerRanking:
    """Dealer ranking with average premiums."""
    dealer: Dealer
    avg_premium_percent: float
    products_tracked: int
    best_for: List[str]  # Categories where this dealer excels

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dealer': self.dealer.to_dict(),
            'avg_premium_percent': self.avg_premium_percent,
            'products_tracked': self.products_tracked,
            'best_for': self.best_for,
        }


class PremiumTrackerDB:
    """Database interface for premium tracker data."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        try:
            # Dealers table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dealers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    website TEXT NOT NULL,
                    shipping_info TEXT,
                    min_free_shipping REAL,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Products table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    metal TEXT NOT NULL,
                    weight_oz REAL NOT NULL,
                    product_type TEXT NOT NULL,
                    mint TEXT,
                    is_government INTEGER DEFAULT 0,
                    typical_premium_low REAL,
                    typical_premium_high REAL
                )
            ''')

            # Prices table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL,
                    dealer_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    spot_price REAL NOT NULL,
                    premium_dollars REAL NOT NULL,
                    premium_percent REAL NOT NULL,
                    in_stock INTEGER DEFAULT 1,
                    product_url TEXT,
                    captured_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (dealer_id) REFERENCES dealers(id)
                )
            ''')

            conn.execute('CREATE INDEX IF NOT EXISTS idx_prices_product ON prices(product_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_prices_dealer ON prices(dealer_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_prices_captured ON prices(captured_at)')

            conn.commit()

            # Check if we need to seed
            cursor = conn.execute('SELECT COUNT(*) FROM dealers')
            if cursor.fetchone()[0] == 0:
                self._seed_data(conn)
        finally:
            conn.close()

    def _seed_data(self, conn: sqlite3.Connection):
        """Seed database with initial data."""
        # Dealers
        dealers = [
            ('apmex', 'APMEX', 'https://www.apmex.com', 'Free shipping over $199', 199.0, 1),
            ('jmbullion', 'JM Bullion', 'https://www.jmbullion.com', 'Free shipping over $199', 199.0, 1),
            ('sdbullion', 'SD Bullion', 'https://www.sdbullion.com', 'Free shipping over $199', 199.0, 1),
            ('moneymetals', 'Money Metals Exchange', 'https://www.moneymetals.com', 'Free shipping over $500', 500.0, 1),
            ('provident', 'Provident Metals', 'https://www.providentmetals.com', 'Free shipping over $199', 199.0, 1),
            ('bgasc', 'BGASC', 'https://www.bgasc.com', 'Free shipping over $99', 99.0, 1),
            ('herobullion', 'Hero Bullion', 'https://www.herobullion.com', '$8.95 flat rate', None, 1),
            ('boldpm', 'Bold Precious Metals', 'https://www.boldpreciousmetals.com', 'Free shipping over $199', 199.0, 1),
        ]

        for dealer in dealers:
            conn.execute('''
                INSERT OR IGNORE INTO dealers (id, name, website, shipping_info, min_free_shipping, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', dealer)

        # Products
        products = [
            # Gold products
            ('gold-eagle-1oz', 'American Gold Eagle', 'gold', 1.0, 'coin', 'US Mint', 1, 4.0, 6.0),
            ('gold-maple-1oz', 'Canadian Gold Maple Leaf', 'gold', 1.0, 'coin', 'Royal Canadian Mint', 1, 3.0, 5.0),
            ('gold-buffalo-1oz', 'American Gold Buffalo', 'gold', 1.0, 'coin', 'US Mint', 1, 4.0, 6.0),
            ('gold-philharmonic-1oz', 'Austrian Gold Philharmonic', 'gold', 1.0, 'coin', 'Austrian Mint', 1, 3.0, 5.0),
            ('gold-krugerrand-1oz', 'South African Krugerrand', 'gold', 1.0, 'coin', 'South African Mint', 1, 3.0, 5.0),
            ('gold-bar-1oz', '1 oz Gold Bar (Various)', 'gold', 1.0, 'bar', None, 0, 2.0, 4.0),
            ('gold-bar-10oz', '10 oz Gold Bar', 'gold', 10.0, 'bar', None, 0, 2.0, 3.0),
            ('gold-bar-kilo', '1 Kilo Gold Bar', 'gold', 32.15, 'bar', None, 0, 1.0, 2.0),

            # Silver products
            ('silver-eagle-1oz', 'American Silver Eagle', 'silver', 1.0, 'coin', 'US Mint', 1, 25.0, 40.0),
            ('silver-maple-1oz', 'Canadian Silver Maple Leaf', 'silver', 1.0, 'coin', 'Royal Canadian Mint', 1, 15.0, 25.0),
            ('silver-philharmonic-1oz', 'Austrian Silver Philharmonic', 'silver', 1.0, 'coin', 'Austrian Mint', 1, 15.0, 25.0),
            ('silver-britannia-1oz', 'British Silver Britannia', 'silver', 1.0, 'coin', 'Royal Mint', 1, 15.0, 25.0),
            ('silver-round-1oz', 'Generic Silver Round', 'silver', 1.0, 'round', None, 0, 8.0, 15.0),
            ('silver-bar-10oz', '10 oz Silver Bar', 'silver', 10.0, 'bar', None, 0, 8.0, 12.0),
            ('silver-bar-100oz', '100 oz Silver Bar', 'silver', 100.0, 'bar', None, 0, 5.0, 8.0),
            ('silver-bar-kilo', '1 Kilo Silver Bar', 'silver', 32.15, 'bar', None, 0, 6.0, 10.0),
            ('junk-silver-quarters', '90% Silver Quarters ($1 FV)', 'silver', 0.715, 'junk', 'US Mint', 1, 5.0, 15.0),
            ('junk-silver-dimes', '90% Silver Dimes ($1 FV)', 'silver', 0.715, 'junk', 'US Mint', 1, 5.0, 15.0),
        ]

        for product in products:
            conn.execute('''
                INSERT OR IGNORE INTO products (id, name, metal, weight_oz, product_type, mint, is_government, typical_premium_low, typical_premium_high)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)

        # Seed sample prices (using January 2026 data)
        # Spot prices: Gold ~$4,523, Silver ~$80.65 (verified from Kitco Jan 2026)
        gold_spot = 4523.0
        silver_spot = 80.65

        sample_prices = [
            # Gold Eagles (~5% premium)
            ('gold-eagle-1oz', 'apmex', 4749.0, 1, gold_spot, True),
            ('gold-eagle-1oz', 'jmbullion', 4720.0, 1, gold_spot, True),
            ('gold-eagle-1oz', 'sdbullion', 4705.0, 1, gold_spot, True),
            ('gold-eagle-1oz', 'moneymetals', 4735.0, 1, gold_spot, True),
            ('gold-eagle-1oz', 'provident', 4725.0, 1, gold_spot, True),

            # Gold Maples (~3.5% premium)
            ('gold-maple-1oz', 'apmex', 4690.0, 1, gold_spot, True),
            ('gold-maple-1oz', 'jmbullion', 4665.0, 1, gold_spot, True),
            ('gold-maple-1oz', 'sdbullion', 4655.0, 1, gold_spot, True),
            ('gold-maple-1oz', 'moneymetals', 4678.0, 1, gold_spot, True),

            # Gold Bars (~2.5% premium)
            ('gold-bar-1oz', 'apmex', 4645.0, 1, gold_spot, True),
            ('gold-bar-1oz', 'jmbullion', 4625.0, 1, gold_spot, True),
            ('gold-bar-1oz', 'sdbullion', 4610.0, 1, gold_spot, True),
            ('gold-bar-1oz', 'moneymetals', 4635.0, 1, gold_spot, True),
            ('gold-bar-1oz', 'bgasc', 4615.0, 1, gold_spot, True),

            # Silver Eagles (~30% premium - higher premium on govt coins)
            ('silver-eagle-1oz', 'apmex', 105.0, 1, silver_spot, True),
            ('silver-eagle-1oz', 'jmbullion', 102.0, 1, silver_spot, True),
            ('silver-eagle-1oz', 'sdbullion', 100.50, 1, silver_spot, True),
            ('silver-eagle-1oz', 'moneymetals', 103.0, 1, silver_spot, True),
            ('silver-eagle-1oz', 'provident', 102.50, 1, silver_spot, False),
            ('silver-eagle-1oz', 'bgasc', 101.50, 1, silver_spot, True),

            # Silver Maples (~20% premium)
            ('silver-maple-1oz', 'apmex', 97.0, 1, silver_spot, True),
            ('silver-maple-1oz', 'jmbullion', 95.0, 1, silver_spot, True),
            ('silver-maple-1oz', 'sdbullion', 94.0, 1, silver_spot, True),
            ('silver-maple-1oz', 'moneymetals', 95.50, 1, silver_spot, True),

            # Silver Rounds (~12% premium)
            ('silver-round-1oz', 'apmex', 91.0, 1, silver_spot, True),
            ('silver-round-1oz', 'jmbullion', 89.0, 1, silver_spot, True),
            ('silver-round-1oz', 'sdbullion', 88.50, 1, silver_spot, True),
            ('silver-round-1oz', 'moneymetals', 89.50, 1, silver_spot, True),
            ('silver-round-1oz', 'herobullion', 88.75, 1, silver_spot, True),

            # 10oz Silver Bars (~10% premium)
            ('silver-bar-10oz', 'apmex', 890.0, 1, silver_spot, True),
            ('silver-bar-10oz', 'jmbullion', 875.0, 1, silver_spot, True),
            ('silver-bar-10oz', 'sdbullion', 870.0, 1, silver_spot, True),
            ('silver-bar-10oz', 'moneymetals', 880.0, 1, silver_spot, True),

            # 100oz Silver Bars (~6% premium)
            ('silver-bar-100oz', 'apmex', 8580.0, 1, silver_spot, True),
            ('silver-bar-100oz', 'jmbullion', 8500.0, 1, silver_spot, True),
            ('silver-bar-100oz', 'sdbullion', 8465.0, 1, silver_spot, True),
            ('silver-bar-100oz', 'moneymetals', 8530.0, 1, silver_spot, False),
        ]

        for price_data in sample_prices:
            product_id, dealer_id, price, quantity, spot_price, in_stock = price_data

            # Get product weight
            cursor = conn.execute('SELECT weight_oz FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            weight_oz = row['weight_oz'] if row else 1.0

            melt_value = spot_price * weight_oz
            premium_dollars = price - melt_value
            premium_percent = (premium_dollars / melt_value) * 100

            conn.execute('''
                INSERT INTO prices (product_id, dealer_id, price, quantity, spot_price, premium_dollars, premium_percent, in_stock, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, dealer_id, price, quantity, spot_price,
                  round(premium_dollars, 2), round(premium_percent, 2),
                  1 if in_stock else 0, datetime.utcnow().isoformat()))

        conn.commit()

    def get_products(self, metal: str = None) -> List[Product]:
        """Get all products, optionally filtered by metal."""
        conn = self._get_conn()
        try:
            if metal:
                cursor = conn.execute('SELECT * FROM products WHERE metal = ?', (metal,))
            else:
                cursor = conn.execute('SELECT * FROM products')

            return [self._row_to_product(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a specific product."""
        conn = self._get_conn()
        try:
            cursor = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return self._row_to_product(row) if row else None
        finally:
            conn.close()

    def get_dealers(self, active_only: bool = True) -> List[Dealer]:
        """Get all dealers."""
        conn = self._get_conn()
        try:
            if active_only:
                cursor = conn.execute('SELECT * FROM dealers WHERE is_active = 1')
            else:
                cursor = conn.execute('SELECT * FROM dealers')

            return [self._row_to_dealer(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_dealer(self, dealer_id: str) -> Optional[Dealer]:
        """Get a specific dealer."""
        conn = self._get_conn()
        try:
            cursor = conn.execute('SELECT * FROM dealers WHERE id = ?', (dealer_id,))
            row = cursor.fetchone()
            return self._row_to_dealer(row) if row else None
        finally:
            conn.close()

    def get_latest_prices(self, product_id: str) -> List[Dict[str, Any]]:
        """Get latest prices for a product across all dealers."""
        conn = self._get_conn()
        try:
            # Get most recent price per dealer
            cursor = conn.execute('''
                SELECT p.*, d.name as dealer_name, d.website as dealer_website, d.shipping_info
                FROM prices p
                JOIN dealers d ON p.dealer_id = d.id
                WHERE p.product_id = ?
                AND p.id IN (
                    SELECT MAX(id) FROM prices
                    WHERE product_id = ?
                    GROUP BY dealer_id
                )
                ORDER BY p.price ASC
            ''', (product_id, product_id))

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_comparison(self, product_id: str) -> Optional[DealerComparison]:
        """Get full comparison data for a product."""
        product = self.get_product(product_id)
        if not product:
            return None

        prices = self.get_latest_prices(product_id)
        if not prices:
            return None

        spot_price = prices[0]['spot_price'] if prices else 0
        melt_value = spot_price * product.weight_oz

        # Find best price (in stock)
        best_price = None
        for p in prices:
            if p['in_stock']:
                best_price = p
                break

        return DealerComparison(
            product=product,
            prices=prices,
            best_price=best_price,
            spot_price=spot_price,
            melt_value=melt_value,
        )

    def get_best_deals(self, metal: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get products with lowest current premiums."""
        conn = self._get_conn()
        try:
            if metal:
                cursor = conn.execute('''
                    SELECT p.*, pr.*, d.name as dealer_name, d.website as dealer_website
                    FROM products p
                    JOIN (
                        SELECT product_id, MIN(premium_percent) as min_premium
                        FROM prices
                        WHERE in_stock = 1
                        AND id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                        GROUP BY product_id
                    ) best ON p.id = best.product_id
                    JOIN prices pr ON pr.product_id = best.product_id AND pr.premium_percent = best.min_premium
                    JOIN dealers d ON pr.dealer_id = d.id
                    WHERE p.metal = ?
                    ORDER BY pr.premium_percent ASC
                    LIMIT ?
                ''', (metal, limit))
            else:
                cursor = conn.execute('''
                    SELECT p.*, pr.*, d.name as dealer_name, d.website as dealer_website
                    FROM products p
                    JOIN (
                        SELECT product_id, MIN(premium_percent) as min_premium
                        FROM prices
                        WHERE in_stock = 1
                        AND id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                        GROUP BY product_id
                    ) best ON p.id = best.product_id
                    JOIN prices pr ON pr.product_id = best.product_id AND pr.premium_percent = best.min_premium
                    JOIN dealers d ON pr.dealer_id = d.id
                    ORDER BY pr.premium_percent ASC
                    LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_dealer_leaderboard(self, metal: str = None) -> List[DealerRanking]:
        """Get dealers ranked by average premium."""
        conn = self._get_conn()
        try:
            if metal:
                cursor = conn.execute('''
                    SELECT d.*, AVG(pr.premium_percent) as avg_premium, COUNT(DISTINCT pr.product_id) as products
                    FROM dealers d
                    JOIN prices pr ON d.id = pr.dealer_id
                    JOIN products p ON pr.product_id = p.id
                    WHERE d.is_active = 1 AND p.metal = ?
                    AND pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                    GROUP BY d.id
                    ORDER BY avg_premium ASC
                ''', (metal,))
            else:
                cursor = conn.execute('''
                    SELECT d.*, AVG(pr.premium_percent) as avg_premium, COUNT(DISTINCT pr.product_id) as products
                    FROM dealers d
                    JOIN prices pr ON d.id = pr.dealer_id
                    WHERE d.is_active = 1
                    AND pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                    GROUP BY d.id
                    ORDER BY avg_premium ASC
                ''')

            rankings = []
            for row in cursor.fetchall():
                dealer = self._row_to_dealer(row)
                # Determine what the dealer is best for
                best_for = self._get_dealer_strengths(conn, dealer.id, metal)
                rankings.append(DealerRanking(
                    dealer=dealer,
                    avg_premium_percent=round(row['avg_premium'], 2),
                    products_tracked=row['products'],
                    best_for=best_for,
                ))

            return rankings
        finally:
            conn.close()

    def _get_dealer_strengths(self, conn: sqlite3.Connection, dealer_id: str, metal: str = None) -> List[str]:
        """Determine what product types a dealer excels at."""
        if metal:
            cursor = conn.execute('''
                SELECT p.product_type, AVG(pr.premium_percent) as avg_prem
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.dealer_id = ? AND p.metal = ?
                AND pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                GROUP BY p.product_type
                ORDER BY avg_prem ASC
                LIMIT 2
            ''', (dealer_id, metal))
        else:
            cursor = conn.execute('''
                SELECT p.product_type, AVG(pr.premium_percent) as avg_prem
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.dealer_id = ?
                AND pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                GROUP BY p.product_type
                ORDER BY avg_prem ASC
                LIMIT 2
            ''', (dealer_id,))

        return [row['product_type'].title() + 's' for row in cursor.fetchall()]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        conn = self._get_conn()
        try:
            # Get latest spot prices
            cursor = conn.execute('''
                SELECT p.metal, pr.spot_price
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.id IN (SELECT MAX(id) FROM prices)
                GROUP BY p.metal
            ''')
            spot_prices = {row['metal']: row['spot_price'] for row in cursor.fetchall()}

            # Count products and dealers
            cursor = conn.execute('SELECT COUNT(*) FROM products')
            product_count = cursor.fetchone()[0]

            cursor = conn.execute('SELECT COUNT(*) FROM dealers WHERE is_active = 1')
            dealer_count = cursor.fetchone()[0]

            # Get average premiums by metal
            cursor = conn.execute('''
                SELECT p.metal, AVG(pr.premium_percent) as avg_prem
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.in_stock = 1
                AND pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id, dealer_id)
                GROUP BY p.metal
            ''')
            avg_premiums = {row['metal']: round(row['avg_prem'], 2) for row in cursor.fetchall()}

            # Get last update time
            cursor = conn.execute('SELECT MAX(captured_at) FROM prices')
            last_update = cursor.fetchone()[0]

            return {
                'spot_prices': spot_prices,
                'product_count': product_count,
                'dealer_count': dealer_count,
                'avg_premiums': avg_premiums,
                'last_update': last_update,
            }
        finally:
            conn.close()

    def add_price(self, product_id: str, dealer_id: str, price: float,
                  spot_price: float, in_stock: bool = True, product_url: str = None) -> Optional[int]:
        """Add a new price entry (for manual updates)."""
        product = self.get_product(product_id)
        if not product:
            return None

        melt_value = spot_price * product.weight_oz
        premium_dollars = price - melt_value
        premium_percent = (premium_dollars / melt_value) * 100

        conn = self._get_conn()
        try:
            cursor = conn.execute('''
                INSERT INTO prices (product_id, dealer_id, price, quantity, spot_price,
                                   premium_dollars, premium_percent, in_stock, product_url, captured_at)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
            ''', (product_id, dealer_id, price, spot_price,
                  round(premium_dollars, 2), round(premium_percent, 2),
                  1 if in_stock else 0, product_url, datetime.utcnow().isoformat()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def reseed(self) -> int:
        """Clear all data and reseed."""
        conn = self._get_conn()
        try:
            conn.execute('DELETE FROM prices')
            conn.execute('DELETE FROM products')
            conn.execute('DELETE FROM dealers')
            conn.commit()
            self._seed_data(conn)

            cursor = conn.execute('SELECT COUNT(*) FROM prices')
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        return Product(
            id=row['id'],
            name=row['name'],
            metal=row['metal'],
            weight_oz=row['weight_oz'],
            product_type=row['product_type'],
            mint=row['mint'],
            is_government=bool(row['is_government']),
            typical_premium_low=row['typical_premium_low'],
            typical_premium_high=row['typical_premium_high'],
        )

    def _row_to_dealer(self, row: sqlite3.Row) -> Dealer:
        return Dealer(
            id=row['id'],
            name=row['name'],
            website=row['website'],
            shipping_info=row['shipping_info'],
            min_free_shipping=row['min_free_shipping'],
            is_active=bool(row['is_active']),
        )


# Singleton instance
_db_instance: Optional[PremiumTrackerDB] = None

def get_premium_db() -> PremiumTrackerDB:
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = PremiumTrackerDB()
    return _db_instance
