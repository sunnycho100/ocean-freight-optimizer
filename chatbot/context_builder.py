"""
Analyze the user's question, pull relevant data, and build
the context that gets sent to the LLM.
"""
import re
from .data_loader import FreightDataLoader


class ContextBuilder:
    def __init__(self, data_loader: FreightDataLoader):
        self.data = data_loader
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        destinations = self.data.get_all_destinations()
        container_types = self.data.get_container_types()
        data_summary = self.data.summarize_data()

        return (
            "You are a freight rate assistant for the Ocean Freight Optimizer system. "
            "You help users find the best shipping routes, compare carrier rates, and understand freight costs.\n\n"
            "Available carriers: ONE Line, HAPAG-Lloyd\n"
            "Data fields for ONE Line: Destination, POD (Port of Discharge), Transport Mode, "
            "Inland Rate, Ocean Rate, Total Rate, Currency, Cost Rank\n"
            "Data fields for HAPAG: From, To, Via, Description (charge types like Ocean Freight, "
            "Destination Landfreight, THC, ISPS), Currency, 20STD, 40STD, 40HC rates\n\n"
            f"Available container types: {', '.join(container_types) if container_types else 'N/A'}\n"
            f"Number of destinations: {len(destinations)}\n"
            f"Data summary: {data_summary}\n\n"
            "Rules:\n"
            "- Answer ONLY based on the provided data. Do not make up rates or routes.\n"
            "- If data is not available for a query, say so clearly.\n"
            "- Format currency values with proper symbols (€ for EUR, $ for USD).\n"
            "- When comparing carriers, present data in a clear structured format.\n"
            "- Be concise but thorough."
        )

    def _detect_intent(self, message: str) -> dict:
        """Parse the user message to detect intent and extract filters."""
        msg_lower = message.lower()
        intent = {
            'type': 'general',
            'destination': None,
            'container_type': None,
            'carrier': None,
        }

        # Detect carrier
        if 'hapag' in msg_lower:
            intent['carrier'] = 'hapag'
        if re.search(r'\bone\b', msg_lower) and 'one line' in msg_lower or re.search(r'\bone\s', msg_lower):
            intent['carrier'] = 'one'

        # Detect comparison intent
        if any(w in msg_lower for w in ['compare', 'vs', 'versus', 'comparison', 'difference']):
            intent['type'] = 'comparison'

        # Detect cheapest/best intent
        elif any(w in msg_lower for w in ['cheapest', 'lowest', 'best', 'minimum', 'min']):
            intent['type'] = 'cheapest'

        # Detect listing intent
        elif any(w in msg_lower for w in ['all', 'list', 'show', 'available']):
            intent['type'] = 'list'

        # Detect destination
        all_destinations = self.data.get_all_destinations()
        for dest in all_destinations:
            # Match by full name or key parts of the destination name
            dest_parts = [p.strip().lower() for p in dest.replace(',', ' ').split() if len(p.strip()) > 2]
            for part in dest_parts:
                if part in msg_lower and part not in ('germany', 'france', 'netherlands', 'belgium',
                                                       'italy', 'spain', 'poland', 'austria',
                                                       'finland', 'sweden', 'norway', 'denmark',
                                                       'the', 'and', 'for'):
                    intent['destination'] = dest
                    break
            if intent['destination']:
                break

        # Detect container type
        container_types = self.data.get_container_types()
        for ct in container_types:
            ct_lower = ct.lower()
            # Check for common abbreviations
            if '40hc' in msg_lower.replace(' ', '') or '40 hc' in msg_lower:
                if 'high cube' in ct_lower:
                    intent['container_type'] = ct
                    break
            elif '40std' in msg_lower.replace(' ', '') or '40 std' in msg_lower or '40ft standard' in msg_lower:
                if '40' in ct_lower and 'standard' in ct_lower:
                    intent['container_type'] = ct
                    break
            elif '20std' in msg_lower.replace(' ', '') or '20 std' in msg_lower or '20ft' in msg_lower:
                if '20' in ct_lower:
                    intent['container_type'] = ct
                    break
            elif ct_lower in msg_lower:
                intent['container_type'] = ct
                break

        return intent

    def _format_one_data(self, routes) -> str:
        """Format ONE route data as text for the LLM context."""
        if routes.empty:
            return "No ONE Line data available for this query."
        lines = ["ONE Line Routes:"]
        for _, row in routes.head(10).iterrows():
            lines.append(
                f"  - {row['Destination']} | {row['Container Type & Size']} | "
                f"POD: {row['POD']} | Mode: {row['Transport Mode']} | "
                f"Inland: {row['Currency']} {row['Rate']} | "
                f"Ocean: {row['Currency']} {row['Ocean Rate']} | "
                f"Total: {row['Currency']} {row['Total Rate']} | "
                f"Rank: {int(row['Cost Rank'])}"
            )
        return "\n".join(lines)

    def _format_hapag_data(self, charges) -> str:
        """Format HAPAG charge data as text for the LLM context."""
        if charges.empty:
            return "No HAPAG data available for this query."
        lines = ["HAPAG-Lloyd Charges:"]
        first = charges.iloc[0]
        lines.append(f"  Route: {first['From']} → {first['To']}" +
                     (f" via {first['Via']}" if str(first['Via']).strip() else ""))
        for _, row in charges.iterrows():
            desc = str(row['Description'])
            curr = str(row['Curr.']) if str(row['Curr.']).strip() else ''
            vals = []
            for col, label in [('20STD', '20STD'), ('40STD', '40STD'), ('40HC', '40HC')]:
                v = str(row[col]) if str(row[col]).strip() and str(row[col]) != 'nan' else '-'
                vals.append(f"{label}: {curr} {v}" if curr else f"{label}: {v}")
            lines.append(f"  - {desc}: {' | '.join(vals)}")
        return "\n".join(lines)

    def build_context(self, user_message: str, history: list = None) -> list:
        """
        Build the messages list to send to the LLM.
        Returns list of dicts with role/content keys.
        """
        intent = self._detect_intent(user_message)

        # Gather relevant data
        data_parts = []

        if intent['type'] == 'comparison' and intent['destination']:
            comparison = self.data.compare_carriers(intent['destination'], intent['container_type'])
            if 'one' in comparison:
                one_routes = self.data.get_routes(intent['destination'], intent['container_type'])
                data_parts.append(self._format_one_data(one_routes))
            if 'hapag' in comparison:
                hapag_charges = self.data.get_hapag_charges(intent['destination'])
                data_parts.append(self._format_hapag_data(hapag_charges))

        elif intent['destination']:
            if intent['carrier'] != 'hapag':
                one_routes = self.data.get_routes(intent['destination'], intent['container_type'])
                data_parts.append(self._format_one_data(one_routes))
            if intent['carrier'] != 'one':
                hapag_charges = self.data.get_hapag_charges(intent['destination'])
                data_parts.append(self._format_hapag_data(hapag_charges))

        elif intent['type'] == 'general':
            # No destination detected — provide summary
            data_parts.append(f"Data Overview:\n{self.data.summarize_data()}")
            dests = self.data.get_all_destinations()
            if dests:
                data_parts.append(f"Available destinations: {', '.join(dests[:30])}"
                                  + (f" ... and {len(dests) - 30} more" if len(dests) > 30 else ""))

        data_context = "\n\n".join(data_parts) if data_parts else "No specific data matched."

        messages = [{"role": "system", "content": self.system_prompt}]

        # Include conversation history if provided (for multi-turn)
        if history:
            for msg in history[-10:]:  # Keep last 10 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add data context + user message
        messages.append({
            "role": "user",
            "content": f"Relevant data:\n{data_context}\n\nUser question: {user_message}"
        })

        return messages
