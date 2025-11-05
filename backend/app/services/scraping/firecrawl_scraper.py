"""
Firecrawl Scraper - Advanced scraper for JavaScript-heavy sites and company career pages
Uses Firecrawl API for intelligent web scraping with AI-powered extraction
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.schemas.job import JobCreate

from .base_scraper import BaseScraper, RateLimiter

logger = logging.getLogger(__name__)
settings = get_settings()


class FirecrawlScraper(BaseScraper):
	"""
	Scraper using Firecrawl for JavaScript-heavy sites and structured data extraction

	Firecrawl advantages:
	- Handles JavaScript rendering automatically
	- AI-powered data extraction
	- Returns structured markdown/JSON
	- Built-in rate limiting
	- Waits for page load automatically
	"""

	def __init__(self, rate_limiter: Optional[RateLimiter] = None, api_key: Optional[str] = None):
		super().__init__(rate_limiter)

		# Get API key from settings or parameter
		self.api_key = api_key or getattr(settings, "FIRECRAWL_API_KEY", None)

		if not self.api_key:
			raise ValueError("Firecrawl API key not found. Set FIRECRAWL_API_KEY in .env")

		# Updated to v2 API
		self.base_url = "https://api.firecrawl.dev/v2"
		self.name = "Firecrawl"

		logger.info(f"✅ Firecrawl v2 API initialized with key: {self.api_key[:10]}...{self.api_key[-4:]}")

		# EU-based companies with strong track record of hiring international talent
		# Focus: Tech companies in EU with visa sponsorship history
		# Expanded to 100+ companies across all EU countries
		self.target_companies = {
			# Netherlands - Tech Hub with 30% ruling tax benefit
			"spotify": {
				"url": "https://www.lifeatspotify.com/jobs",
				"name": "Spotify",
				"location": "Stockholm, Sweden / Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"adyen": {
				"url": "https://careers.adyen.com/vacancies",
				"name": "Adyen",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data Science", "Analytics", "Engineering"],
			},
			"booking": {
				"url": "https://careers.booking.com/",
				"name": "Booking.com",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"mollie": {
				"url": "https://jobs.mollie.com/",
				"name": "Mollie",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Product"],
			},
			"tomtom": {
				"url": "https://www.tomtom.com/careers/jobs/",
				"name": "TomTom",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			# Germany - EU Blue Card available
			"klarna": {
				"url": "https://jobs.lever.co/klarna",
				"name": "Klarna",
				"location": "Stockholm, Sweden / Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"n26": {
				"url": "https://n26.com/en/careers",
				"name": "N26",
				"location": "Berlin, Germany / Barcelona, Spain",
				"visa_sponsor": True,
				"filters": ["Data", "Analytics", "Engineering"],
			},
			"zalando": {
				"url": "https://jobs.zalando.com/en/",
				"name": "Zalando",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"delivery_hero": {
				"url": "https://careers.deliveryhero.com/global/en",
				"name": "Delivery Hero",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"soundcloud": {
				"url": "https://careers.soundcloud.com/",
				"name": "SoundCloud",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering"],
			},
			"sap": {
				"url": "https://jobs.sap.com/",
				"name": "SAP",
				"location": "Walldorf, Germany / Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering", "Cloud"],
			},
			# UK - Skilled Worker Visa
			"deepmind_london": {
				"url": "https://www.deepmind.com/careers",
				"name": "DeepMind",
				"location": "London, UK / Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Research", "AI", "ML"],
			},
			"revolut": {
				"url": "https://www.revolut.com/careers/",
				"name": "Revolut",
				"location": "London, UK / Vilnius, Lithuania",
				"visa_sponsor": True,
				"filters": ["Data", "Analytics", "Engineering"],
			},
			"monzo": {
				"url": "https://monzo.com/careers/",
				"name": "Monzo",
				"location": "London, UK / Cardiff, UK",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering"],
			},
			"transferwise": {
				"url": "https://www.wise.com/jobs/",
				"name": "Wise (TransferWise)",
				"location": "London, UK / Tallinn, Estonia",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"babylon_health": {
				"url": "https://www.babylonhealth.com/careers",
				"name": "Babylon Health",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "AI", "Health Tech"],
			},
			# Sweden - Strong tech ecosystem
			"northvolt": {
				"url": "https://careers.northvolt.com/jobs",
				"name": "Northvolt",
				"location": "Stockholm, Sweden",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Analytics"],
			},
			# Estonia - E-Residency friendly
			"bolt": {
				"url": "https://bolt.eu/en/careers/positions/",
				"name": "Bolt",
				"location": "Tallinn, Estonia / Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			# Ireland - Tech hub with IDA support
			"stripe_dublin": {
				"url": "https://stripe.com/jobs",
				"name": "Stripe",
				"location": "Dublin, Ireland / London, UK",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"zendesk": {
				"url": "https://jobs.zendesk.com/",
				"name": "Zendesk",
				"location": "Dublin, Ireland",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Analytics"],
			},
			# France - French Tech Visa
			"blablacar": {
				"url": "https://www.blablacar.com/careers",
				"name": "BlaBlaCar",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"dataiku": {
				"url": "https://www.dataiku.com/careers/",
				"name": "Dataiku",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			# Spain - Tech startup visa
			"cabify": {
				"url": "https://cabify.com/careers",
				"name": "Cabify",
				"location": "Madrid, Spain",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"glovo": {
				"url": "https://jobs.glovoapp.com/",
				"name": "Glovo",
				"location": "Barcelona, Spain",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			# Switzerland - High salaries, work permits available
			"google_zurich": {
				"url": "https://careers.google.com/jobs/results/?location=Zurich",
				"name": "Google Zurich",
				"location": "Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering", "Research"],
			},
			"uber_zurich": {
				"url": "https://www.uber.com/careers/list/?location=Zurich",
				"name": "Uber",
				"location": "Zurich, Switzerland / Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			# Portugal - Tech visa program
			"farfetch": {
				"url": "https://www.farfetch.com/careers",
				"name": "Farfetch",
				"location": "Porto, Portugal / Lisbon, Portugal",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"feedzai": {
				"url": "https://careers.feedzai.com/",
				"name": "Feedzai",
				"location": "Lisbon, Portugal",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "AI"],
			},
			# ============= EXPANDED: 70+ MORE COMPANIES =============
			# NETHERLANDS (30% Ruling) - More Companies
			"elastic": {
				"url": "https://www.elastic.co/careers",
				"name": "Elastic",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Search"],
			},
			"bunq": {
				"url": "https://www.bunq.com/careers",
				"name": "bunq",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Engineering", "Product", "Data"],
			},
			"messagebird": {
				"url": "https://messagebird.com/careers",
				"name": "MessageBird",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Platform"],
			},
			"catawiki": {
				"url": "https://www.catawiki.com/careers",
				"name": "Catawiki",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			"picnic": {
				"url": "https://picnic.app/careers",
				"name": "Picnic",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering", "Logistics"],
			},
			"backbase": {
				"url": "https://www.backbase.com/careers",
				"name": "Backbase",
				"location": "Amsterdam, Netherlands",
				"visa_sponsor": True,
				"filters": ["Engineering", "Product", "Cloud"],
			},
			# GERMANY (EU Blue Card) - More Companies
			"contentful": {
				"url": "https://www.contentful.com/careers/",
				"name": "Contentful",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Engineering", "Product", "Data"],
			},
			"gorillas": {
				"url": "https://gorillas.io/en/careers",
				"name": "Gorillas",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Operations"],
			},
			"tier_mobility": {
				"url": "https://www.tier.app/careers",
				"name": "TIER Mobility",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Mobility"],
			},
			"personio": {
				"url": "https://www.personio.com/careers/",
				"name": "Personio",
				"location": "Munich, Germany",
				"visa_sponsor": True,
				"filters": ["Engineering", "Product", "Data"],
			},
			"celonis": {
				"url": "https://www.celonis.com/careers",
				"name": "Celonis",
				"location": "Munich, Germany",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			"flixbus": {
				"url": "https://www.flixbus.com/company/careers",
				"name": "FlixBus",
				"location": "Munich, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Analytics"],
			},
			"siemens": {
				"url": "https://jobs.siemens.com/",
				"name": "Siemens",
				"location": "Munich, Germany / Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "IoT", "AI"],
			},
			"bmw_group": {
				"url": "https://www.bmwgroup.jobs/",
				"name": "BMW Group",
				"location": "Munich, Germany",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Autonomous Driving"],
			},
			"auto1": {
				"url": "https://www.auto1-group.com/careers",
				"name": "AUTO1 Group",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"wefox": {
				"url": "https://www.wefox.com/careers",
				"name": "wefox",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "InsurTech"],
			},
			"adjust": {
				"url": "https://www.adjust.com/careers/",
				"name": "Adjust",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data", "Analytics", "Engineering"],
			},
			"hellofresh": {
				"url": "https://www.hellofreshgroup.com/careers",
				"name": "HelloFresh",
				"location": "Berlin, Germany",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			# UK (Skilled Worker Visa) - More Companies
			"checkout": {
				"url": "https://www.checkout.com/careers",
				"name": "Checkout.com",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Fintech"],
			},
			"thought_machine": {
				"url": "https://thoughtmachine.net/careers",
				"name": "Thought Machine",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Banking"],
			},
			"starling_bank": {
				"url": "https://www.starlingbank.com/careers/",
				"name": "Starling Bank",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Fintech"],
			},
			"deliveroo": {
				"url": "https://careers.deliveroo.co.uk/",
				"name": "Deliveroo",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			"octopus_energy": {
				"url": "https://octopus.energy/careers",
				"name": "Octopus Energy",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Energy Tech"],
			},
			"bulb": {
				"url": "https://bulb.co.uk/careers",
				"name": "Bulb",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Clean Tech"],
			},
			"improbable": {
				"url": "https://www.improbable.io/careers",
				"name": "Improbable",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Metaverse"],
			},
			"darktrace": {
				"url": "https://darktrace.com/careers",
				"name": "Darktrace",
				"location": "Cambridge, UK / London, UK",
				"visa_sponsor": True,
				"filters": ["AI", "ML", "Cybersecurity"],
			},
			"benevolent_ai": {
				"url": "https://www.benevolent.com/careers",
				"name": "BenevolentAI",
				"location": "London, UK",
				"visa_sponsor": True,
				"filters": ["AI", "ML", "Drug Discovery"],
			},
			# SWEDEN - More Companies
			"king": {
				"url": "https://www.king.com/careers",
				"name": "King (Activision Blizzard)",
				"location": "Stockholm, Sweden",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Gaming"],
			},
			"ericsson": {
				"url": "https://www.ericsson.com/careers",
				"name": "Ericsson",
				"location": "Stockholm, Sweden",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "5G", "IoT"],
			},
			"volvo": {
				"url": "https://www.volvogroup.com/careers",
				"name": "Volvo Group",
				"location": "Gothenburg, Sweden",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Autonomous Driving"],
			},
			"truecaller": {
				"url": "https://www.truecaller.com/careers",
				"name": "Truecaller",
				"location": "Stockholm, Sweden",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			# IRELAND - More Companies
			"intercom": {
				"url": "https://www.intercom.com/careers",
				"name": "Intercom",
				"location": "Dublin, Ireland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Product"],
			},
			"workday": {
				"url": "https://www.workday.com/careers",
				"name": "Workday",
				"location": "Dublin, Ireland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Cloud"],
			},
			"hubspot": {
				"url": "https://www.hubspot.com/careers",
				"name": "HubSpot",
				"location": "Dublin, Ireland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Marketing Tech"],
			},
			"indeed_dublin": {
				"url": "https://www.indeed.jobs/career",
				"name": "Indeed",
				"location": "Dublin, Ireland",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "Engineering"],
			},
			# FRANCE - More Companies
			"doctolib": {
				"url": "https://careers.doctolib.com/",
				"name": "Doctolib",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "HealthTech"],
			},
			"contentsquare": {
				"url": "https://contentsquare.com/careers/",
				"name": "Contentsquare",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Data", "Analytics", "Engineering"],
			},
			"deezer": {
				"url": "https://www.deezer.com/careers",
				"name": "Deezer",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Music Tech"],
			},
			"criteo": {
				"url": "https://www.criteo.com/careers/",
				"name": "Criteo",
				"location": "Paris, France",
				"visa_sponsor": True,
				"filters": ["Data Science", "ML", "AdTech"],
			},
			# SPAIN - More Companies
			"typeform": {
				"url": "https://www.typeform.com/careers/",
				"name": "Typeform",
				"location": "Barcelona, Spain",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Product"],
			},
			"wallapop": {
				"url": "https://es.wallapop.com/about/careers",
				"name": "Wallapop",
				"location": "Barcelona, Spain",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"travelperk": {
				"url": "https://www.travelperk.com/careers",
				"name": "TravelPerk",
				"location": "Barcelona, Spain",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Travel Tech"],
			},
			# DENMARK - More Companies
			"unity_copenhagen": {
				"url": "https://careers.unity.com/",
				"name": "Unity Technologies",
				"location": "Copenhagen, Denmark",
				"visa_sponsor": True,
				"filters": ["Engineering", "ML", "Gaming"],
			},
			"maersk": {
				"url": "https://www.maersk.com/careers",
				"name": "Maersk",
				"location": "Copenhagen, Denmark",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Logistics"],
			},
			"zendesk_copenhagen": {
				"url": "https://jobs.zendesk.com/",
				"name": "Zendesk Copenhagen",
				"location": "Copenhagen, Denmark",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data"],
			},
			# FINLAND
			"supercell": {
				"url": "https://supercell.com/careers",
				"name": "Supercell",
				"location": "Helsinki, Finland",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Gaming"],
			},
			"wolt": {
				"url": "https://careers.wolt.com/",
				"name": "Wolt",
				"location": "Helsinki, Finland",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Delivery"],
			},
			"reaktor": {
				"url": "https://www.reaktor.com/careers",
				"name": "Reaktor",
				"location": "Helsinki, Finland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Consulting"],
			},
			# NORWAY
			"kahoot": {
				"url": "https://kahoot.com/careers/",
				"name": "Kahoot!",
				"location": "Oslo, Norway",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "EdTech"],
			},
			"vipps": {
				"url": "https://www.vipps.no/om-oss/ledige-stillinger/",
				"name": "Vipps",
				"location": "Oslo, Norway",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Fintech"],
			},
			# SWITZERLAND - More Companies
			"google_switzerland": {
				"url": "https://careers.google.com/jobs/results/?location=Switzerland",
				"name": "Google Switzerland",
				"location": "Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Research", "ML"],
			},
			"facebook_zurich": {
				"url": "https://www.metacareers.com/jobs/?offices=Zurich",
				"name": "Meta (Facebook)",
				"location": "Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Engineering", "AI", "ML", "Data"],
			},
			"microsoft_zurich": {
				"url": "https://careers.microsoft.com/",
				"name": "Microsoft Zurich",
				"location": "Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Engineering", "AI", "Research"],
			},
			"digitalocean_zurich": {
				"url": "https://www.digitalocean.com/careers",
				"name": "DigitalOcean",
				"location": "Zurich, Switzerland",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Cloud"],
			},
			# PORTUGAL - More Companies
			"outsystems": {
				"url": "https://www.outsystems.com/careers/",
				"name": "OutSystems",
				"location": "Lisbon, Portugal",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "Low-code"],
			},
			"talkdesk": {
				"url": "https://www.talkdesk.com/careers/",
				"name": "Talkdesk",
				"location": "Porto, Portugal / Lisbon, Portugal",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "AI"],
			},
			# POLAND
			"allegro": {
				"url": "https://allegro.pl/praca",
				"name": "Allegro",
				"location": "Warsaw, Poland / Krakow, Poland",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Engineering"],
			},
			"revolut_poland": {
				"url": "https://www.revolut.com/careers/",
				"name": "Revolut Poland",
				"location": "Krakow, Poland",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Fintech"],
			},
			# BELGIUM
			"collibra": {
				"url": "https://www.collibra.com/careers",
				"name": "Collibra",
				"location": "Brussels, Belgium",
				"visa_sponsor": True,
				"filters": ["Data", "Engineering", "Data Governance"],
			},
			# AUSTRIA
			"runtastic": {
				"url": "https://www.runtastic.com/careers",
				"name": "Runtastic (Adidas)",
				"location": "Vienna, Austria",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Health Tech"],
			},
			# ESTONIA - More Companies
			"pipedrive": {
				"url": "https://www.pipedrive.com/careers",
				"name": "Pipedrive",
				"location": "Tallinn, Estonia",
				"visa_sponsor": True,
				"filters": ["Engineering", "Data", "CRM"],
			},
			"taxify": {
				"url": "https://bolt.eu/en/careers/",
				"name": "Bolt (Taxify)",
				"location": "Tallinn, Estonia",
				"visa_sponsor": True,
				"filters": ["Data", "ML", "Mobility"],
			},
		}

	async def search_jobs(
		self,
		keywords: str = "AI Data Science",
		location: str = "Europe",
		max_results: int = 25,
		companies: Optional[List[str]] = None,
	) -> List[JobCreate]:
		"""
		Scrape jobs using Firecrawl from company career pages

		Args:
			keywords: Job search keywords
			location: Location filter (used for filtering results)
			max_results: Maximum number of jobs to return
			companies: List of company names to scrape (defaults to all)

		Returns:
			List of JobCreate objects
		"""
		logger.info(f"Starting Firecrawl job search for '{keywords}' in {location}")

		jobs = []

		# Determine which companies to scrape
		if companies:
			target_companies = {k: v for k, v in self.target_companies.items() if k in companies}
		else:
			target_companies = self.target_companies

		# Scrape each company's career page
		for company_key, company_info in target_companies.items():
			if len(jobs) >= max_results:
				break

			try:
				logger.info(f"Scraping {company_info['name']} careers page...")
				company_jobs = await self._scrape_company_page(
					company_info,
					keywords,
					location,
					max_results - len(jobs),
				)

				jobs.extend(company_jobs)
				logger.info(f"Found {len(company_jobs)} jobs from {company_info['name']}")

			except Exception as e:
				logger.error(f"Error scraping {company_info['name']}: {e}", exc_info=True)
				continue

		logger.info(f"Firecrawl search completed: {len(jobs)} jobs found")
		return jobs[:max_results]

	async def _scrape_company_page(
		self,
		company_info: Dict[str, Any],
		keywords: str,
		location: str,
		max_results: int,
	) -> List[JobCreate]:
		"""Extract jobs from company career page using Firecrawl v2 /extract endpoint"""

		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		jobs = []

		try:
			url = company_info["url"]
			company_location = company_info.get("location", "Europe")
			visa_sponsor = company_info.get("visa_sponsor", False)

			# Define JSON schema for job extraction with EU-specific fields
			job_schema = {
				"type": "object",
				"properties": {
					"jobs": {
						"type": "array",
						"items": {
							"type": "object",
							"properties": {
								"title": {"type": "string", "description": "Job title or position name"},
								"location": {
									"type": "string",
									"description": "Specific city and country in EU (e.g., 'Berlin, Germany', 'Amsterdam, Netherlands')",
								},
								"description": {"type": "string", "description": "Job description including responsibilities and qualifications"},
								"url": {"type": "string", "description": "Direct link to apply for this specific job"},
								"job_type": {"type": "string", "description": "Full-time, Part-time, Contract, Internship"},
								"remote_option": {"type": "string", "description": "Remote, Hybrid, or On-site"},
								"experience_level": {"type": "string", "description": "Entry-level, Mid-level, Senior, or Lead"},
								"skills_required": {
									"type": "array",
									"items": {"type": "string"},
									"description": "Key technical skills or tools required",
								},
								"visa_sponsorship": {
									"type": "boolean",
									"description": "True if visa/work permit sponsorship is explicitly mentioned",
								},
								"relocation_support": {"type": "boolean", "description": "True if relocation assistance is mentioned"},
							},
							"required": ["title", "location"],
						},
					}
				},
				"required": ["jobs"],
			}

			# Build EU-focused extraction prompt
			eu_countries = "Germany, Netherlands, UK, Sweden, France, Ireland, Spain, Switzerland, Austria, Denmark, Estonia, Lithuania, Poland, Czech Republic, Finland, Norway"

			extract_params = {
				"urls": [url],
				"prompt": f"""Extract job listings that match these criteria:

LOCATION FILTER: Only include jobs based in EU countries ({eu_countries}). 
Company's EU offices: {company_location}

KEYWORDS: {keywords} (Data Science, Machine Learning, AI, Analytics, Engineering)

VISA/INTERNATIONAL HIRING: This company has a history of sponsoring work visas: {visa_sponsor}
- Look for mentions of: "visa sponsorship", "work permit", "right to work", "relocation package", "international candidates welcome"
- Include jobs that explicitly support international hiring

EXPERIENCE LEVELS: Include all levels (Entry, Mid, Senior, Lead)

REQUIRED INFORMATION per job:
- Exact job title
- Specific EU city and country
- Job description with key responsibilities
- Required technical skills (Python, SQL, ML, etc.)
- Experience level required
- Whether visa sponsorship is mentioned
- Whether relocation support is offered
- Direct application URL if available

EXCLUDE:
- Jobs outside EU
- US-only positions
- Roles requiring existing EU work authorization without sponsorship""",
				"schema": job_schema,
			}

			# Make API request to Firecrawl v2 /extract endpoint
			headers = {
				"Authorization": f"Bearer {self.api_key}",
				"Content-Type": "application/json",
			}

			logger.info(f"Starting extraction job for {company_info['name']}...")

			response = await self._make_request(
				f"{self.base_url}/extract",
				method="POST",
				headers=headers,
				json=extract_params,
			)

			if not response:
				logger.warning(f"Failed to start extraction for {company_info['name']}")
				return []

			# Parse initial response to get job ID
			data = response.json()

			if not data.get("success"):
				error_msg = data.get("error", "Unknown error")
				logger.warning(f"Firecrawl /extract returned error for {company_info['name']}: {error_msg}")
				return []

			# Get the job ID
			job_id = data.get("id")
			if not job_id:
				logger.warning(f"No job ID returned for {company_info['name']}")
				return []

			logger.info(f"Extraction job started for {company_info['name']}, ID: {job_id}")

			# Poll for results (max 180 seconds, check every 5 seconds)
			import asyncio

			max_polls = 36  # 36 polls * 5 seconds = 180 seconds = 3 minutes
			poll_interval = 5

			for attempt in range(max_polls):
				await asyncio.sleep(poll_interval)

				# Check job status
				status_response = await self._make_request(
					f"{self.base_url}/extract/{job_id}",
					method="GET",
					headers=headers,
				)

				if not status_response:
					logger.warning(f"Failed to get status for job {job_id}")
					continue

				status_data = status_response.json()

				if not status_data.get("success"):
					logger.warning(f"Status check failed for job {job_id}")
					continue

				job_status = status_data.get("status", "")

				if job_status == "completed":
					logger.info(f"Extraction completed for {company_info['name']}")

					# Extract the data
					extracted_data = status_data.get("data", {})

					if isinstance(extracted_data, dict) and "jobs" in extracted_data:
						jobs = self._parse_jobs_from_json(extracted_data, company_info, keywords, location, max_results)
					else:
						logger.warning(f"No jobs found in extracted data for {company_info['name']}")

					break

				elif job_status == "failed":
					error = status_data.get("error", "Unknown error")
					logger.error(f"Extraction failed for {company_info['name']}: {error}")
					break

				elif job_status == "processing":
					logger.debug(f"Extraction still processing for {company_info['name']} (attempt {attempt + 1}/{max_polls})")
					continue
				else:
					logger.debug(f"Extraction status '{job_status}' for {company_info['name']}")

			if not jobs:
				logger.warning(f"No jobs extracted from {company_info['name']} after {max_polls * poll_interval} seconds")

		except Exception as e:
			logger.error(f"Error in _scrape_company_page for {company_info['name']}: {e}", exc_info=True)

		return jobs

	def _parse_jobs_from_json(
		self,
		json_data: Dict[str, Any],
		company_info: Dict[str, Any],
		keywords: str,
		location: str,
		max_results: int,
	) -> List[JobCreate]:
		"""Parse job listings from Firecrawl v2 JSON extraction"""

		jobs = []

		try:
			# JSON structure can vary, try common patterns
			job_listings = []

			# Try to find jobs array in various possible keys
			if isinstance(json_data, list):
				job_listings = json_data
			elif "jobs" in json_data:
				job_listings = json_data["jobs"]
			elif "listings" in json_data:
				job_listings = json_data["listings"]
			elif "positions" in json_data:
				job_listings = json_data["positions"]
			elif "data" in json_data:
				job_listings = json_data["data"]

			if not isinstance(job_listings, list):
				logger.debug(f"No job listings found in JSON for {company_info['name']}")
				return []

			logger.info(f"Found {len(job_listings)} jobs in JSON extraction from {company_info['name']}")

			# Parse each job from JSON
			for job_data in job_listings[:max_results]:
				if len(jobs) >= max_results:
					break

				try:
					# Extract fields (handle various key names)
					title = (job_data.get("title") or job_data.get("position") or job_data.get("job_title") or job_data.get("name", "")).strip()

					if not title or len(title) < 5:
						continue

					# Filter by keywords
					if keywords:
						keyword_list = keywords.lower().split()
						title_lower = title.lower()
						description_text = str(job_data.get("description", "")).lower()

						has_keyword = any(kw in title_lower or kw in description_text for kw in keyword_list)
						if not has_keyword:
							continue

					# Extract location
					job_location = job_data.get("location") or job_data.get("office") or job_data.get("city") or "Remote / Europe"

					if isinstance(job_location, dict):
						job_location = f"{job_location.get('city', '')}, {job_location.get('country', '')}".strip(", ")

					job_location = str(job_location).strip()

					# Extract description
					description = str(job_data.get("description", "") or job_data.get("summary", "")).strip()

					# Extract skills if available
					skills = job_data.get("skills_required", [])
					if skills and isinstance(skills, list):
						# Add skills to description
						skills_text = ", ".join(skills[:10])  # Limit to 10 skills
						if skills_text and description:
							description = f"{description}\n\nKey Skills: {skills_text}"

					# Extract experience level
					experience_level = job_data.get("experience_level", "")
					if experience_level and description:
						description = f"[{experience_level}] {description}"

					# Check for visa sponsorship (enhanced)
					visa_terms = ["visa sponsor", "sponsorship", "work permit", "visa support", "relocation", "international candidates"]
					requires_visa = (
						job_data.get("visa_sponsorship", False)
						or job_data.get("relocation_support", False)
						or any(term in description.lower() for term in visa_terms)
					)

					# Skip jobs that explicitly require existing EU work authorization without sponsorship
					if any(
						phrase in description.lower()
						for phrase in ["must have eu work authorization", "existing right to work required", "no visa sponsorship"]
					):
						logger.debug(f"Skipping job (no sponsorship): {title}")
						continue

					# Extract URL if available
					job_url = job_data.get("url") or job_data.get("link") or job_data.get("application_url") or company_info["url"]

					# Remote option
					remote_option = job_data.get("remote_option", "on-site").lower()
					if not remote_option or remote_option == "on-site":
						remote_text = str(job_data.get("remote", "")).lower()
						if "remote" in remote_text or "remote" in description.lower():
							remote_option = "remote"
						elif "hybrid" in remote_text or "hybrid" in description.lower():
							remote_option = "hybrid"
						else:
							remote_option = "on-site"

					# Job type
					job_type = job_data.get("job_type") or job_data.get("type") or "Full-time"

					# Job type
					job_type = job_data.get("job_type") or job_data.get("type") or "Full-time"

					# Create job object
					job = JobCreate(
						title=title,
						company=company_info["name"],
						location=job_location,
						description=description or f"{title} at {company_info['name']} - {company_info.get('location', 'EU')}",
						application_url=job_url,
						source="Firecrawl",
						job_type=job_type,
						remote_option=remote_option,
						salary_min=None,
						salary_max=None,
						currency="EUR",  # EU companies typically pay in EUR
						requires_visa_sponsorship=requires_visa,
					)

					jobs.append(job)

				except Exception as e:
					logger.debug(f"Error parsing individual job from JSON: {e}")
					continue

		except Exception as e:
			logger.error(f"Error parsing jobs from JSON: {e}", exc_info=True)

		return jobs

	def _parse_jobs_from_content(
		self,
		content: str,
		company_info: Dict[str, Any],
		keywords: str,
		location: str,
		max_results: int,
	) -> List[JobCreate]:
		"""Parse job listings from markdown/HTML content"""

		jobs = []

		try:
			# Split content into potential job sections
			# Look for common patterns in career pages

			# Pattern 1: Job titles in headers (markdown style)
			job_sections = re.split(r"\n#{1,3}\s+", content)

			keyword_list = keywords.lower().split()
			location_terms = location.lower().split()

			for section in job_sections:
				if len(jobs) >= max_results:
					break

				# Check if section contains relevant keywords
				section_lower = section.lower()

				# Must contain at least one keyword
				has_keyword = any(kw in section_lower for kw in keyword_list)
				if not has_keyword:
					continue

				# Try to extract job information
				job = self._extract_job_from_section(section, company_info)

				if job:
					# Additional filtering for location if specified
					if location and location.lower() != "europe":
						job_location_lower = job.location.lower()
						if not any(term in job_location_lower for term in location_terms):
							# Check if remote
							if "remote" not in section_lower and "worldwide" not in section_lower:
								continue

					jobs.append(job)

		except Exception as e:
			logger.error(f"Error parsing jobs from content: {e}", exc_info=True)

		return jobs

	def _extract_job_from_section(
		self,
		section: str,
		company_info: Dict[str, Any],
	) -> Optional[JobCreate]:
		"""Extract job details from a content section"""

		try:
			lines = section.strip().split("\n")
			if not lines:
				return None

			# First line is usually the title
			title = lines[0].strip().strip("#").strip()

			if not title or len(title) < 5:
				return None

			# Look for location in the content
			location = "Remote / Europe"  # Default
			for line in lines[1:10]:  # Check first few lines
				line_lower = line.lower()
				if any(term in line_lower for term in ["location", "where", "office", "based"]):
					# Extract location
					location_match = re.search(r"location[:\s]+([^,\n]+)", line, re.IGNORECASE)
					if location_match:
						location = location_match.group(1).strip()
					break

			# Check for visa sponsorship mentions
			content_lower = section.lower()
			requires_visa = any(
				term in content_lower
				for term in [
					"visa sponsor",
					"sponsorship",
					"work permit",
					"right to work",
					"visa support",
				]
			)

			# Extract description (rest of content)
			description = "\n".join(lines[1:]).strip()

			# Truncate description if too long
			if len(description) > 2000:
				description = description[:2000] + "..."

			# Build job URL
			job_url = company_info["url"]

			# Try to find specific job URL in content
			url_match = re.search(r"https?://[^\s\)]+", section)
			if url_match:
				job_url = url_match.group(0)

			job = JobCreate(
				title=title,
				company=company_info["name"],
				location=location,
				description=description or f"{title} at {company_info['name']}",
				url=job_url,
				source="Firecrawl",
				job_type="Full-time",  # Default assumption
				remote_option="remote" if "remote" in content_lower else "hybrid",
				posted_date=datetime.now(),
				salary_min=None,
				salary_max=None,
				salary_currency="USD",  # Default for most tech companies
				requires_visa_sponsorship=requires_visa,
			)

			return job

		except Exception as e:
			logger.error(f"Error extracting job from section: {e}", exc_info=True)
			return None

	async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[Any]:
		"""Override to support POST requests and API authentication"""
		if not self.session:
			raise RuntimeError("Scraper must be used as async context manager")

		await self.rate_limiter.wait()

		try:
			# For Firecrawl API calls, use provided headers directly
			# Don't mix browser headers with API authentication
			if "headers" not in kwargs:
				kwargs["headers"] = self._get_headers()

			logger.debug(f"Making {method} request to: {url}")
			logger.debug(f"Headers: {kwargs['headers']}")

			if method.upper() == "POST":
				response = await self.session.post(url, **kwargs)
			else:
				response = await self.session.get(url, **kwargs)

			response.raise_for_status()
			return response

		except Exception as e:
			logger.error(f"Request error for {url}: {e}")
			return None

	def close(self):
		"""Close the scraper session"""
		if self.session:
			import asyncio

			try:
				loop = asyncio.get_event_loop()
				if loop.is_running():
					self._close_tasks = getattr(self, "_close_tasks", [])
					self._close_tasks.append(loop.create_task(self.session.aclose()))
				else:
					loop.run_until_complete(self.session.aclose())
			except Exception:
				pass

	# Abstract methods implementation (required by BaseScraper)
	def _build_search_url(self, keywords: str, location: str, page: int = 0) -> str:
		"""Not used - Firecrawl scrapes specific company pages"""
		return ""

	def _parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
		"""Not used - Firecrawl uses AI-powered JSON extraction"""
		return None
