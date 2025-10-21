"""
Precedent seeder service for populating the vector database with sample legal precedents.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List

from ..core.logging import get_logger
from .vector_store_service import VectorStoreService, get_vector_store_service

logger = get_logger(__name__)


class PrecedentSeederService:
    """Service for seeding the vector database with legal precedents."""
    
    def __init__(self, vector_store: VectorStoreService = None):
        """Initialize precedent seeder service."""
        self.vector_store = vector_store or get_vector_store_service()
    
    def get_sample_precedents(self) -> List[Dict]:
        """Get comprehensive sample legal precedents for seeding."""
        return [
            # Liability Limitation Clauses
            {
                "text": "The Company shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or business interruption, regardless of the theory of liability.",
                "category": "liability_limitation",
                "risk_level": "High",
                "source_document": "Standard Service Agreement Template",
                "effectiveness_score": 0.85,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Technology",
                    "clause_type": "broad_limitation"
                }
            },
            {
                "text": "In no event shall either party's liability exceed the total amount paid by Customer under this Agreement in the twelve (12) months preceding the claim.",
                "category": "liability_limitation",
                "risk_level": "Medium",
                "source_document": "SaaS Agreement Template",
                "effectiveness_score": 0.75,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Software",
                    "clause_type": "monetary_cap"
                }
            },
            {
                "text": "Company's total liability for all claims arising under this Agreement shall not exceed $10,000 or the amount paid by Customer in the preceding year, whichever is greater.",
                "category": "liability_limitation",
                "risk_level": "Medium",
                "source_document": "Professional Services Agreement",
                "effectiveness_score": 0.70,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Professional Services",
                    "clause_type": "specific_cap"
                }
            },
            
            # Termination Clauses
            {
                "text": "Either party may terminate this agreement at any time without cause by providing thirty (30) days written notice to the other party.",
                "category": "termination",
                "risk_level": "Medium",
                "source_document": "Software License Agreement",
                "effectiveness_score": 0.60,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Software",
                    "clause_type": "mutual_termination"
                }
            },
            {
                "text": "This Agreement may be terminated immediately by either party upon written notice if the other party materially breaches this Agreement and fails to cure such breach within fifteen (15) days after written notice.",
                "category": "termination",
                "risk_level": "Low",
                "source_document": "Consulting Agreement",
                "effectiveness_score": 0.80,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Consulting",
                    "clause_type": "breach_termination"
                }
            },
            {
                "text": "Customer may terminate this Agreement for convenience with ninety (90) days written notice. Company may terminate for non-payment after thirty (30) days notice and opportunity to cure.",
                "category": "termination",
                "risk_level": "Medium",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.65,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Services",
                    "clause_type": "asymmetric_termination"
                }
            },
            
            # Indemnification Clauses
            {
                "text": "Customer shall indemnify, defend, and hold harmless the Company from and against any and all claims, damages, losses, costs, and expenses arising from Customer's use of the services or breach of this Agreement.",
                "category": "indemnification",
                "risk_level": "High",
                "source_document": "SaaS Agreement Template",
                "effectiveness_score": 0.90,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Technology",
                    "clause_type": "broad_indemnification"
                }
            },
            {
                "text": "Each party shall indemnify the other against third-party claims arising from such party's gross negligence or willful misconduct in the performance of this Agreement.",
                "category": "indemnification",
                "risk_level": "Low",
                "source_document": "Mutual Service Agreement",
                "effectiveness_score": 0.70,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "General",
                    "clause_type": "mutual_indemnification"
                }
            },
            {
                "text": "Company shall indemnify Customer against claims that the Services infringe any third-party intellectual property rights, provided Customer promptly notifies Company and cooperates in the defense.",
                "category": "indemnification",
                "risk_level": "Medium",
                "source_document": "Software License Agreement",
                "effectiveness_score": 0.75,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Software",
                    "clause_type": "ip_indemnification"
                }
            },
            
            # Intellectual Property Clauses
            {
                "text": "All intellectual property rights in the deliverables, including but not limited to copyrights, patents, trade secrets, and trademarks, shall vest exclusively in the Company.",
                "category": "intellectual_property",
                "risk_level": "High",
                "source_document": "Consulting Agreement",
                "effectiveness_score": 0.85,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Consulting",
                    "clause_type": "work_for_hire"
                }
            },
            {
                "text": "Customer retains all rights to its pre-existing intellectual property. Company retains all rights to its pre-existing intellectual property and any improvements thereto.",
                "category": "intellectual_property",
                "risk_level": "Low",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.60,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Services",
                    "clause_type": "retained_rights"
                }
            },
            {
                "text": "Any intellectual property developed jointly by the parties shall be owned jointly, with each party having the right to use and license such intellectual property without accounting to the other.",
                "category": "intellectual_property",
                "risk_level": "Medium",
                "source_document": "Joint Development Agreement",
                "effectiveness_score": 0.55,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Technology",
                    "clause_type": "joint_ownership"
                }
            },
            
            # Payment Terms Clauses
            {
                "text": "Payment terms are net 30 days from invoice date. Late payments shall incur a service charge of 1.5% per month or the maximum rate permitted by law, whichever is less.",
                "category": "payment_terms",
                "risk_level": "Low",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.70,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Services",
                    "clause_type": "standard_terms"
                }
            },
            {
                "text": "All fees are due and payable in advance. Company may suspend services immediately upon non-payment without notice.",
                "category": "payment_terms",
                "risk_level": "High",
                "source_document": "SaaS Agreement",
                "effectiveness_score": 0.80,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Software",
                    "clause_type": "prepayment_required"
                }
            },
            {
                "text": "Customer shall pay all undisputed invoices within fifteen (15) days. Disputed amounts must be raised in writing within ten (10) days of invoice receipt.",
                "category": "payment_terms",
                "risk_level": "Medium",
                "source_document": "Professional Services Agreement",
                "effectiveness_score": 0.65,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Professional Services",
                    "clause_type": "dispute_process"
                }
            },
            
            # Confidentiality Clauses
            {
                "text": "Each party acknowledges that it may receive confidential information and agrees to maintain such information in strict confidence for a period of five (5) years following termination of this Agreement.",
                "category": "confidentiality",
                "risk_level": "Medium",
                "source_document": "Non-Disclosure Agreement",
                "effectiveness_score": 0.75,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "General",
                    "clause_type": "mutual_confidentiality"
                }
            },
            {
                "text": "Customer's confidential information shall be protected with the same degree of care Company uses for its own confidential information, but in no event less than reasonable care.",
                "category": "confidentiality",
                "risk_level": "Low",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.60,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Services",
                    "clause_type": "standard_care"
                }
            },
            {
                "text": "All information disclosed by Company shall be deemed confidential unless specifically marked otherwise. Recipient shall not disclose such information to any third party without prior written consent.",
                "category": "confidentiality",
                "risk_level": "High",
                "source_document": "Technology License Agreement",
                "effectiveness_score": 0.85,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Technology",
                    "clause_type": "broad_confidentiality"
                }
            },
            
            # Warranty Clauses
            {
                "text": "THE SERVICES ARE PROVIDED 'AS IS' WITHOUT WARRANTY OF ANY KIND. COMPANY DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.",
                "category": "warranty",
                "risk_level": "High",
                "source_document": "Software License Agreement",
                "effectiveness_score": 0.90,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Software",
                    "clause_type": "disclaimer"
                }
            },
            {
                "text": "Company warrants that the Services will be performed in a professional and workmanlike manner in accordance with industry standards.",
                "category": "warranty",
                "risk_level": "Medium",
                "source_document": "Professional Services Agreement",
                "effectiveness_score": 0.65,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Professional Services",
                    "clause_type": "performance_warranty"
                }
            },
            {
                "text": "Company represents and warrants that it has the full right, power, and authority to enter into this Agreement and perform its obligations hereunder.",
                "category": "warranty",
                "risk_level": "Low",
                "source_document": "General Service Agreement",
                "effectiveness_score": 0.50,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "General",
                    "clause_type": "authority_warranty"
                }
            },
            
            # Force Majeure Clauses
            {
                "text": "Neither party shall be liable for any failure or delay in performance due to circumstances beyond its reasonable control, including acts of God, war, terrorism, pandemic, or government action.",
                "category": "force_majeure",
                "risk_level": "Low",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.70,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "General",
                    "clause_type": "standard_force_majeure"
                }
            },
            {
                "text": "Force majeure events include natural disasters, labor disputes, supplier failures, and any other cause beyond a party's reasonable control that prevents performance for more than thirty (30) days.",
                "category": "force_majeure",
                "risk_level": "Medium",
                "source_document": "Supply Agreement",
                "effectiveness_score": 0.65,
                "metadata": {
                    "jurisdiction": "US",
                    "industry": "Manufacturing",
                    "clause_type": "detailed_force_majeure"
                }
            },
            
            # Governing Law Clauses
            {
                "text": "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of laws principles.",
                "category": "governing_law",
                "risk_level": "Low",
                "source_document": "Corporate Agreement",
                "effectiveness_score": 0.80,
                "metadata": {
                    "jurisdiction": "Delaware",
                    "industry": "General",
                    "clause_type": "state_law"
                }
            },
            {
                "text": "Any disputes arising under this Agreement shall be resolved exclusively in the state and federal courts located in New York County, New York.",
                "category": "governing_law",
                "risk_level": "Medium",
                "source_document": "Service Agreement",
                "effectiveness_score": 0.75,
                "metadata": {
                    "jurisdiction": "New York",
                    "industry": "General",
                    "clause_type": "jurisdiction_clause"
                }
            }
        ]
    
    def seed_precedents(self, force_reseed: bool = False) -> Dict:
        """
        Seed the vector database with sample precedents.
        
        Args:
            force_reseed: If True, clear existing data and reseed
            
        Returns:
            Dictionary with seeding results
        """
        try:
            # Check if already seeded
            stats = self.vector_store.get_collection_stats()
            existing_count = stats.get("total_clauses", 0)
            
            if existing_count > 0 and not force_reseed:
                logger.info(f"Vector database already contains {existing_count} precedents. Use force_reseed=True to reseed.")
                return {
                    "status": "skipped",
                    "message": f"Database already contains {existing_count} precedents",
                    "existing_count": existing_count
                }
            
            # Get sample precedents
            sample_precedents = self.get_sample_precedents()
            
            # Add precedents to vector store
            added_count = 0
            failed_count = 0
            
            for precedent_data in sample_precedents:
                try:
                    clause_id = self.vector_store.add_precedent_clause(
                        text=precedent_data["text"],
                        category=precedent_data["category"],
                        risk_level=precedent_data["risk_level"],
                        source_document=precedent_data["source_document"],
                        effectiveness_score=precedent_data["effectiveness_score"],
                        metadata=precedent_data.get("metadata", {})
                    )
                    added_count += 1
                    logger.debug(f"Added precedent clause: {clause_id}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to add precedent clause: {e}")
            
            # Get final stats
            final_stats = self.vector_store.get_collection_stats()
            
            result = {
                "status": "completed",
                "added_count": added_count,
                "failed_count": failed_count,
                "total_precedents": final_stats.get("total_clauses", 0),
                "categories": final_stats.get("categories", {}),
                "risk_levels": final_stats.get("risk_levels", {})
            }
            
            logger.info(f"Precedent seeding completed: {added_count} added, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Failed to seed precedents: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def export_precedents_to_json(self, file_path: str) -> bool:
        """Export current precedents to JSON file."""
        try:
            # Get all precedents
            all_results = self.vector_store.collection.get(include=["documents", "metadatas"])
            
            precedents_data = []
            if all_results["documents"]:
                for i, doc in enumerate(all_results["documents"]):
                    precedent = {
                        "id": all_results["ids"][i],
                        "text": doc,
                        "metadata": all_results["metadatas"][i] if all_results["metadatas"] else {}
                    }
                    precedents_data.append(precedent)
            
            # Write to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(precedents_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(precedents_data)} precedents to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export precedents: {e}")
            return False
    
    def import_precedents_from_json(self, file_path: str) -> Dict:
        """Import precedents from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                precedents_data = json.load(f)
            
            added_count = 0
            failed_count = 0
            
            for precedent in precedents_data:
                try:
                    metadata = precedent.get("metadata", {})
                    
                    clause_id = self.vector_store.add_precedent_clause(
                        text=precedent["text"],
                        category=metadata.get("category", "unknown"),
                        risk_level=metadata.get("risk_level", "unknown"),
                        source_document=metadata.get("source_document", "imported"),
                        effectiveness_score=metadata.get("effectiveness_score", 0.5),
                        metadata=metadata
                    )
                    added_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to import precedent: {e}")
            
            return {
                "status": "completed",
                "added_count": added_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logger.error(f"Failed to import precedents: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }


# Global instance
_precedent_seeder_service = None


def get_precedent_seeder_service() -> PrecedentSeederService:
    """Get global precedent seeder service instance."""
    global _precedent_seeder_service
    if _precedent_seeder_service is None:
        _precedent_seeder_service = PrecedentSeederService()
    return _precedent_seeder_service