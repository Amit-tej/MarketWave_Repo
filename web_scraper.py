import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import time
import re
from typing import Dict, List, Optional, Tuple
import logging
from utils import get_logger

logger = get_logger("web_scraper")

# Fix for importlib.metadata issue in older Python versions
try:
    from importlib.metadata import packages_distributions
except ImportError:
    # Fallback for older Python versions
    def packages_distributions():
        return {}


class CommodityPriceScraper:
    def __init__(self, gemini_api_key: str, cse_id: str = "8572491c823e44e56"):
        self.gemini_api_key = gemini_api_key
        self.cse_id = cse_id
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-pro")

        # Headers to mimic a real browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _duckduckgo_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search using DuckDuckGo (no API key required)"""
        try:
            # Try different import paths for duckduckgo_search
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                try:
                    from ddgs import DDGS
                except ImportError:
                    # Try direct import if installed differently
                    import duckduckgo_search

                    DDGS = duckduckgo_search.DDGS

            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=num_results)
                for r in search_results:
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        }
                    )

            return results[:num_results]

        except ImportError as ie:
            logger.error(
                f"duckduckgo_search import failed: {ie}, falling back to direct search"
            )
            raise Exception("DuckDuckGo search not available")
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise

    def search_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """Search for commodity prices using multiple fallback methods"""
        try:
            # Try DuckDuckGo search first (no API key required)
            return self._duckduckgo_search(query, num_results)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            # Fallback to direct Google scraping
            return self._fallback_google_search(query, num_results)

    def _fallback_google_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Fallback Google search using direct scraping"""
        try:
            # Use a more direct approach - search for known agricultural price websites
            known_sites = [
                "https://agmarknet.gov.in/",
                "https://www.commodityonline.com/",
                "https://www.krishimaratavahini.kar.nic.in/",
                "https://www.agricoop.nic.in/",
            ]

            results = []
            for site in known_sites[:num_results]:
                results.append(
                    {
                        "title": f"Agricultural Market Prices - {site.split('//')[1].split('.')[0]}",
                        "url": site,
                        "snippet": f"Current market prices for agricultural commodities from {site}",
                    }
                )

            # Add some generic search results
            generic_queries = [
                f"https://www.google.com/search?q={query.replace(' ', '+')}",
                f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            ]

            for url in generic_queries:
                if len(results) < num_results:
                    results.append(
                        {
                            "title": f"Search results for {query}",
                            "url": url,
                            "snippet": f"Web search results for current {query}",
                        }
                    )

            return results[:num_results]

        except Exception as e:
            logger.error(f"Fallback Google search failed: {e}")
            return []

    def scrape_price_from_url(self, url: str) -> str:
        """Scrape content from a specific URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return ""

    def extract_prices_with_gemini(
        self, content: str, commodity: str, market: str = ""
    ) -> Dict:
        """Use Gemini AI to extract prices from scraped content"""

        prompt = f"""
        Extract current market prices for {commodity} from the following web content.
        Focus on finding actual price information in rupees per kg or per quintal.
        Look for patterns like:
        - ₹X/kg or ₹X per kg
        - ₹X/quintal or ₹X per quintal
        - Price ranges like ₹X-Y/kg
        - Current market rates
        - Today's prices

        If market is specified as "{market}", prioritize prices from that market.

        Content:
        {content[:4000]}  # Limit content length

        Return a JSON object with:
        {{
            "current_price": number or null,
            "price_range": {{"min": number, "max": number}} or null,
            "unit": "kg" or "quintal",
            "market": "market name" or null,
            "confidence": number between 0-1,
            "source": "brief description of source"
        }}

        If no prices found, return {{"current_price": null, "price_range": null, "unit": null, "market": null, "confidence": 0, "source": null}}
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response to extract JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            # Parse JSON
            result = json.loads(result_text)
            return result

        except Exception as e:
            logger.error(f"Gemini price extraction failed: {e}")
            return {
                "current_price": None,
                "price_range": None,
                "unit": None,
                "market": None,
                "confidence": 0,
                "source": None,
            }

    def get_commodity_price(
        self, commodity: str, market: str = "", max_searches: int = 3
    ) -> Dict:
        """Get current price for a commodity using web search and Gemini AI"""

        # Create search queries
        queries = [
            f"{commodity} price today {market} india",
            f"{commodity} current market rate {market}",
            f"{commodity} wholesale price {market} rupees",
        ]

        all_prices = []

        for query in queries[:max_searches]:
            logger.info(f"Searching for: {query}")

            # Search Google
            search_results = self.search_google(query, num_results=5)

            for result in search_results:
                # Scrape the page content
                content = self.scrape_price_from_url(result["url"])
                if not content:
                    continue

                # Extract prices using Gemini
                price_data = self.extract_prices_with_gemini(content, commodity, market)

                if price_data.get("current_price") or price_data.get("price_range"):
                    price_data["search_query"] = query
                    price_data["url"] = result["url"]
                    all_prices.append(price_data)

                # Rate limiting
                time.sleep(1)

        # Aggregate results
        if not all_prices:
            return {
                "commodity": commodity,
                "market": market,
                "current_price": None,
                "price_range": None,
                "unit": None,
                "confidence": 0,
                "sources": [],
                "timestamp": time.time(),
            }

        # Find the most confident result
        best_result = max(all_prices, key=lambda x: x.get("confidence", 0))

        # If we have multiple results, calculate average
        if len(all_prices) > 1:
            valid_prices = [p for p in all_prices if p.get("current_price")]
            if valid_prices:
                avg_price = sum(p["current_price"] for p in valid_prices) / len(
                    valid_prices
                )
                best_result["average_price"] = avg_price

        return {
            "commodity": commodity,
            "market": market,
            "current_price": best_result.get("current_price"),
            "price_range": best_result.get("price_range"),
            "unit": best_result.get("unit"),
            "confidence": best_result.get("confidence", 0),
            "sources": [
                {"url": p["url"], "confidence": p.get("confidence", 0)}
                for p in all_prices
            ],
            "timestamp": time.time(),
        }

    def get_multiple_commodities_prices(
        self, commodities: List[str], market: str = ""
    ) -> Dict[str, Dict]:
        """Get prices for multiple commodities"""
        results = {}

        for commodity in commodities:
            logger.info(f"Getting price for {commodity}")
            results[commodity] = self.get_commodity_price(commodity, market)

            # Rate limiting between commodities
            time.sleep(2)

        return results

    def generate_search_queries_with_gemini(
        self, commodity: str, market: str = "", data_type: str = "historical"
    ) -> List[str]:
        """Use Gemini AI to generate optimized search queries for historical or forecast data"""

        if data_type == "historical":
            prompt = f"""
            Generate 5 optimized search queries to find historical price data for {commodity} in {market if market else "Indian markets"}.
            Focus on finding price trends, historical data, price charts, and market analysis from the past 1-2 years.

            Prioritize these agricultural market websites:
            - agmarknet.gov.in (official government portal)
            - commodityonline.com
            - krishimaratavahini.kar.nic.in
            - agricoop.nic.in
            - ceda.ac.in (Centre for Economic and Social Studies)
            - Government agricultural portals and statistical departments

            Include site-specific searches like "site:agmarknet.gov.in {commodity} price history"

            Return only the search queries as a JSON array of strings, no explanations.
            """
        elif data_type == "forecast":
            prompt = f"""
            Generate 5 optimized search queries to find price forecast data for {commodity} in {market if market else "Indian markets"}.
            Focus on finding price predictions, market outlook, seasonal forecasts, and expert analysis for the next 3-6 months.

            Prioritize these agricultural market websites:
            - agmarknet.gov.in (official government portal)
            - commodityonline.com
            - krishimaratavahini.kar.nic.in
            - agricoop.nic.in
            - ceda.ac.in (Centre for Economic and Social Studies)
            - Government agricultural portals and statistical departments

            Include site-specific searches like "site:agmarknet.gov.in {commodity} price forecast"

            Return only the search queries as a JSON array of strings, no explanations.
            """
        else:
            return []

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response to extract JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()
            queries = json.loads(result_text)

            if isinstance(queries, list):
                return queries[:5]  # Limit to 5 queries
            else:
                return []

        except Exception as e:
            logger.error(f"Gemini query generation failed: {e}")
            # Fallback queries
            if data_type == "historical":
                return [
                    f"{commodity} historical price data {market} india",
                    f"{commodity} price trends {market} past year",
                    f"{commodity} market analysis {market} historical data",
                    f"{commodity} price chart {market} india",
                    f"{commodity} agricultural statistics {market}",
                ]
            else:
                return [
                    f"{commodity} price forecast {market} india",
                    f"{commodity} market outlook {market} next months",
                    f"{commodity} price prediction {market} india",
                    f"{commodity} seasonal forecast {market}",
                    f"{commodity} agricultural forecast {market} india",
                ]

    def extract_historical_data_with_gemini(
        self, content: str, commodity: str, market: str = ""
    ) -> Dict:
        """Use Gemini AI to extract historical price data from content"""

        prompt = f"""
        Extract historical price data for {commodity} from the following web content.
        Look for price trends, historical data points, and market analysis from the past 1-2 years.

        Focus on finding:
        - Monthly or weekly price averages
        - Price ranges (min/max) over time periods
        - Seasonal trends and patterns
        - Year-over-year comparisons
        - Market-specific data for {market if market else "various markets"}

        Content:
        {content[:5000]}  # Limit content length

        Return a JSON object with:
        {{
            "historical_prices": [
                {{
                    "date": "YYYY-MM-DD or period description",
                    "price": number,
                    "unit": "kg" or "quintal",
                    "market": "market name",
                    "source": "brief description"
                }}
            ],
            "trends": {{
                "seasonal_pattern": "description of seasonal trends",
                "price_range": {{"min": number, "max": number}},
                "average_price": number,
                "volatility": "high/medium/low"
            }},
            "confidence": number between 0-1,
            "data_points": number
        }}

        If no historical data found, return {{"historical_prices": [], "trends": null, "confidence": 0, "data_points": 0}}
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response to extract JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()
            result = json.loads(result_text)
            return result

        except Exception as e:
            logger.error(f"Gemini historical data extraction failed: {e}")
            return {
                "historical_prices": [],
                "trends": None,
                "confidence": 0,
                "data_points": 0,
            }

    def extract_forecast_data_with_gemini(
        self, content: str, commodity: str, market: str = ""
    ) -> Dict:
        """Use Gemini AI to extract forecast price data from content"""

        prompt = f"""
        Extract price forecast data for {commodity} from the following web content.
        Look for predictions, market outlook, and expert analysis for the next 3-6 months.

        Focus on finding:
        - Short-term price predictions (1-3 months)
        - Medium-term forecasts (3-6 months)
        - Factors affecting price movement
        - Market outlook and expert opinions
        - Seasonal forecast adjustments

        Content:
        {content[:5000]}  # Limit content length

        Return a JSON object with:
        {{
            "forecasts": [
                {{
                    "period": "next 1 month" or "next 3 months" etc.,
                    "predicted_price": number,
                    "price_range": {{"min": number, "max": number}},
                    "unit": "kg" or "quintal",
                    "confidence": number between 0-1,
                    "factors": ["factor1", "factor2"],
                    "source": "brief description"
                }}
            ],
            "market_outlook": {{
                "trend": "increasing/decreasing/stable",
                "key_factors": ["factor1", "factor2"],
                "risk_level": "high/medium/low"
            }},
            "overall_confidence": number between 0-1,
            "forecast_horizon": "months"
        }}

        If no forecast data found, return {{"forecasts": [], "market_outlook": null, "overall_confidence": 0, "forecast_horizon": null}}
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up the response to extract JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result_text = result_text.strip()
            result = json.loads(result_text)
            return result

        except Exception as e:
            logger.error(f"Gemini forecast data extraction failed: {e}")
            return {
                "forecasts": [],
                "market_outlook": None,
                "overall_confidence": 0,
                "forecast_horizon": None,
            }

    def get_historical_prices(
        self, commodity: str, market: str = "", max_searches: int = 5
    ) -> Dict:
        """Get historical price data for a commodity using web search and Gemini AI"""

        # Generate optimized search queries using Gemini
        queries = self.generate_search_queries_with_gemini(
            commodity, market, "historical"
        )

        all_historical_data = []

        for query in queries[:max_searches]:
            logger.info(f"Searching for historical data: {query}")

            # Search Google
            search_results = self.search_google(query, num_results=5)

            for result in search_results:
                # Scrape the page content
                content = self.scrape_price_from_url(result["url"])
                if not content:
                    continue

                # Extract historical data using Gemini
                historical_data = self.extract_historical_data_with_gemini(
                    content, commodity, market
                )

                if historical_data.get("historical_prices"):
                    historical_data["search_query"] = query
                    historical_data["url"] = result["url"]
                    all_historical_data.append(historical_data)

                # Rate limiting
                time.sleep(1)

        # Aggregate results
        if not all_historical_data:
            return {
                "commodity": commodity,
                "market": market,
                "historical_prices": [],
                "trends": None,
                "confidence": 0,
                "data_points": 0,
                "sources": [],
                "timestamp": time.time(),
            }

        # Find the most comprehensive result
        best_result = max(
            all_historical_data,
            key=lambda x: x.get("data_points", 0) * x.get("confidence", 0),
        )

        # Combine data from multiple sources if available
        combined_prices = []
        for data in all_historical_data:
            combined_prices.extend(data.get("historical_prices", []))

        # Remove duplicates and sort by date
        seen_dates = set()
        unique_prices = []
        for price in combined_prices:
            date_key = price.get("date", "")
            if date_key not in seen_dates:
                seen_dates.add(date_key)
                unique_prices.append(price)

        unique_prices.sort(key=lambda x: x.get("date", ""), reverse=True)

        return {
            "commodity": commodity,
            "market": market,
            "historical_prices": unique_prices[:50],  # Limit to 50 data points
            "trends": best_result.get("trends"),
            "confidence": best_result.get("confidence", 0),
            "data_points": len(unique_prices),
            "sources": [
                {
                    "url": data["url"],
                    "confidence": data.get("confidence", 0),
                    "data_points": data.get("data_points", 0),
                }
                for data in all_historical_data
            ],
            "timestamp": time.time(),
        }

    def get_forecast_prices(
        self, commodity: str, market: str = "", max_searches: int = 5
    ) -> Dict:
        """Get forecast price data for a commodity using web search and Gemini AI"""

        # Generate optimized search queries using Gemini
        queries = self.generate_search_queries_with_gemini(
            commodity, market, "forecast"
        )

        all_forecast_data = []

        for query in queries[:max_searches]:
            logger.info(f"Searching for forecast data: {query}")

            # Search Google
            search_results = self.search_google(query, num_results=5)

            for result in search_results:
                # Scrape the page content
                content = self.scrape_price_from_url(result["url"])
                if not content:
                    continue

                # Extract forecast data using Gemini
                forecast_data = self.extract_forecast_data_with_gemini(
                    content, commodity, market
                )

                if forecast_data.get("forecasts"):
                    forecast_data["search_query"] = query
                    forecast_data["url"] = result["url"]
                    all_forecast_data.append(forecast_data)

                # Rate limiting
                time.sleep(1)

        # Aggregate results
        if not all_forecast_data:
            return {
                "commodity": commodity,
                "market": market,
                "forecasts": [],
                "market_outlook": None,
                "overall_confidence": 0,
                "forecast_horizon": None,
                "sources": [],
                "timestamp": time.time(),
            }

        # Find the most confident result
        best_result = max(
            all_forecast_data, key=lambda x: x.get("overall_confidence", 0)
        )

        # Combine forecasts from multiple sources
        combined_forecasts = []
        for data in all_forecast_data:
            combined_forecasts.extend(data.get("forecasts", []))

        # Remove duplicates based on period
        seen_periods = set()
        unique_forecasts = []
        for forecast in combined_forecasts:
            period_key = forecast.get("period", "")
            if period_key not in seen_periods:
                seen_periods.add(period_key)
                unique_forecasts.append(forecast)

        unique_forecasts.sort(key=lambda x: x.get("period", ""))

        return {
            "commodity": commodity,
            "market": market,
            "forecasts": unique_forecasts,
            "market_outlook": best_result.get("market_outlook"),
            "overall_confidence": best_result.get("overall_confidence", 0),
            "forecast_horizon": best_result.get("forecast_horizon"),
            "sources": [
                {"url": data["url"], "confidence": data.get("overall_confidence", 0)}
                for data in all_forecast_data
            ],
            "timestamp": time.time(),
        }

    def get_price_comparison(self, commodity: str, markets: List[str] = None) -> Dict:
        """Get price comparison data across multiple markets for a commodity"""
        if markets is None:
            # Default major Indian agricultural markets
            markets = [
                "Hyderabad",
                "Mumbai",
                "Delhi",
                "Bangalore",
                "Chennai",
                "Kolkata",
                "Pune",
                "Ahmedabad",
                "Jaipur",
                "Lucknow",
            ]

        logger.info(
            f"Getting price comparison for {commodity} across {len(markets)} markets"
        )

        market_prices = []
        successful_fetches = 0

        for market in markets:
            try:
                logger.info(f"Fetching price for {commodity} in {market}")
                price_data = self.get_commodity_price(commodity, market)

                if price_data.get("current_price") is not None:
                    market_prices.append(
                        {
                            "market": market,
                            "price": price_data["current_price"],
                            "unit": price_data.get("unit", "kg"),
                            "confidence": price_data.get("confidence", 0),
                            "timestamp": price_data.get("timestamp", time.time()),
                        }
                    )
                    successful_fetches += 1
                else:
                    # Add entry with null price but keep the market
                    market_prices.append(
                        {
                            "market": market,
                            "price": None,
                            "unit": None,
                            "confidence": 0,
                            "timestamp": time.time(),
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to get price for {market}: {e}")
                market_prices.append(
                    {
                        "market": market,
                        "price": None,
                        "unit": None,
                        "confidence": 0,
                        "timestamp": time.time(),
                    }
                )

            # Rate limiting between market requests
            time.sleep(1)

        # Filter out markets with no price data for calculations
        valid_prices = [mp for mp in market_prices if mp["price"] is not None]

        if not valid_prices:
            return {
                "commodity": commodity,
                "markets_searched": len(markets),
                "successful_fetches": 0,
                "lowest_price": None,
                "lowest_market": None,
                "highest_price": None,
                "highest_market": None,
                "average_price": None,
                "price_range": None,
                "all_prices": market_prices,
                "unit": "kg",
                "timestamp": time.time(),
            }

        # Sort by price to find min/max
        sorted_prices = sorted(valid_prices, key=lambda x: x["price"])
        lowest = sorted_prices[0]
        highest = sorted_prices[-1]

        # Calculate average price
        avg_price = sum(mp["price"] for mp in valid_prices) / len(valid_prices)

        # Determine most common unit
        unit_counts = {}
        for mp in valid_prices:
            unit = mp.get("unit", "kg")
            unit_counts[unit] = unit_counts.get(unit, 0) + 1

        most_common_unit = (
            max(unit_counts.keys(), key=lambda x: unit_counts[x])
            if unit_counts
            else "kg"
        )

        return {
            "commodity": commodity,
            "markets_searched": len(markets),
            "successful_fetches": successful_fetches,
            "lowest_price": lowest["price"],
            "lowest_market": lowest["market"],
            "highest_price": highest["price"],
            "highest_market": highest["market"],
            "average_price": round(avg_price, 2),
            "price_range": {
                "min": lowest["price"],
                "max": highest["price"],
                "spread": round(highest["price"] - lowest["price"], 2),
            },
            "all_prices": market_prices,
            "unit": most_common_unit,
            "price_volatility": self._calculate_price_volatility(valid_prices),
            "timestamp": time.time(),
        }

    def _calculate_price_volatility(self, price_data: List[Dict]) -> str:
        """Calculate price volatility level based on price spread"""
        if len(price_data) < 2:
            return "unknown"

        prices = [mp["price"] for mp in price_data]
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # Calculate coefficient of variation (CV)
        if avg_price > 0:
            cv = (max_price - min_price) / avg_price
            if cv < 0.1:
                return "low"
            elif cv < 0.25:
                return "medium"
            else:
                return "high"
        else:
            return "unknown"


# Global scraper instance
_scraper = None


def get_price_scraper(
    api_key: str = "AIzaSyDKvF_SvdYhzBZBup7-l1vBVWlhnPF_m7g",
) -> CommodityPriceScraper:
    """Get or create scraper instance with Gemini API key"""
    global _scraper
    if _scraper is None:
        _scraper = CommodityPriceScraper(api_key)
    return _scraper


def get_current_commodity_price(commodity: str, market: str = "") -> Dict:
    """Convenience function to get commodity price"""
    scraper = get_price_scraper()
    return scraper.get_commodity_price(commodity, market)


def get_historical_commodity_prices(commodity: str, market: str = "") -> Dict:
    """Convenience function to get historical commodity prices"""
    scraper = get_price_scraper()
    return scraper.get_historical_prices(commodity, market)


def get_forecast_commodity_prices(commodity: str, market: str = "") -> Dict:
    """Convenience function to get forecast commodity prices"""
    scraper = get_price_scraper()
    return scraper.get_forecast_prices(commodity, market)


if __name__ == "__main__":
    # Test the scraper
    scraper = get_price_scraper()
    result = scraper.get_commodity_price("tomato", "Hyderabad")
    print(json.dumps(result, indent=2))
