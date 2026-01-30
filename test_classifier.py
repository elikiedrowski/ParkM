#!/usr/bin/env python3
"""
Test the email classifier with sample ParkM support emails
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.classifier import EmailClassifier
import json

# Sample emails from ParkM support scenarios
SAMPLE_EMAILS = [
    {
        "name": "Simple Refund Request",
        "subject": "Need refund",
        "body": "I moved out last month and you guys charged me. I demand a refund."
    },
    {
        "name": "Complex Refund - Multiple Permits",
        "subject": "Charges and refund",
        "body": """I have two cars registered but I sold one. I also have a guest permit. 
        I moved out 2 months ago but still getting charged. Can you help me figure this out?"""
    },
    {
        "name": "Simple Vehicle Update",
        "subject": "Update plate",
        "body": "I just bought a new car. My new plates 123 ABC. Need to update my permit."
    },
    {
        "name": "Unclear Vehicle Update",
        "subject": "New car",
        "body": "I got a new car. Update my account."
    },
    {
        "name": "Spanish Refund Request",
        "subject": "Reembolso",
        "body": "Me mudé hace un mes. Quiero un reembolso. No vivo más ahí."
    },
    {
        "name": "Angry Customer - High Urgency",
        "subject": "THIS IS RIDICULOUS!!!",
        "body": """I have been trying to cancel for WEEKS and you keep charging me! 
        This is theft! I'm calling my lawyer if I don't get a refund immediately!"""
    },
    {
        "name": "Simple Status Inquiry",
        "subject": "Do I have a permit?",
        "body": "Hi, I'm confused. Do I have a permit for my car? Plate number XYZ 789."
    }
]


def test_classifier():
    """Test the email classifier"""
    print("=" * 80)
    print("Email Classification Test - ParkM Support")
    print("=" * 80)
    print()
    
    classifier = EmailClassifier()
    
    for i, email in enumerate(SAMPLE_EMAILS, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}: {email['name']}")
        print(f"{'=' * 80}")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body'][:100]}{'...' if len(email['body']) > 100 else ''}")
        print()
        print("Classifying...")
        
        result = classifier.classify_email(email['subject'], email['body'])
        
        print("\n📊 CLASSIFICATION RESULTS:")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Complexity: {result.get('complexity')}")
        print(f"  Language: {result.get('language')}")
        print(f"  Urgency: {result.get('urgency')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Requires Refund: {result.get('requires_refund')}")
        print(f"  Requires Human Review: {result.get('requires_human_review')}")
        print(f"  Suggested Response: {result.get('suggested_response_type')}")
        
        if result.get('key_entities'):
            print("\n🔍 KEY ENTITIES:")
            for key, value in result['key_entities'].items():
                if value:
                    print(f"  {key}: {value}")
        
        routing = classifier.get_routing_recommendation(result)
        print(f"\n📮 ROUTING RECOMMENDATION: {routing}")
        
        print(f"\n💡 NOTES: {result.get('notes')}")
        
    print("\n" + "=" * 80)
    print("Classification test complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_classifier()
