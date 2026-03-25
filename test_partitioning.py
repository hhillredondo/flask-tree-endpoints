#!/usr/bin/env python3
"""
Test script for Flask partitioning middleware
"""


def test_partitioning_system():
    """Test the partitioning system"""
    print("🔍 Testing Partitioning System")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    print("\n📋 Test Steps:")
    print("1. Create a tree (generates partition key)")
    print("2. List user's trees")
    print("3. Test partitioned endpoints")
    print("4. Test access control")
    
    print("\n⚠️  Prerequisites:")
    print("   - Flask app running on localhost:5000")
    print("   - Valid JWT token from Amplify")
    print("   - Local Gremlin server running")
    
    print("\n🔑 To get JWT token from Amplify:")
    print("   - Log into your Amplify app")
    print("   - Open browser dev tools (F12)")
    print("   - Go to Network tab")
    print("   - Make any request and copy the Authorization header")
    
    print("\n🧪 Test Commands:")
    print("\n1. Create a tree in Amplify first (get tree_id)")
    print("   Then create first member in Neptune:")
    print(f"   curl -X POST {base_url}/trees \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
    print("        -d '{")
    print("          \"tree_id\": \"YOUR_AMPLIFY_TREE_ID\",")
    print("          \"name\": \"John\",")
    print("          \"surname\": \"Doe\",")
    print("          \"gender\": \"male\",")
    print("          \"description\": \"Tree creator\",")
    print("          \"born\": \"1990-01-01T00:00:00Z\",")
    print("          \"pic\": \"https://example.com/photo.jpg\",")
    print("          \"photos\": \"https://example.com/photos\"")
    print("        }'")
    
    print("\n2. List user's trees:")
    print(f"   curl -X GET {base_url}/trees \\")
    print("        -H 'Authorization: Bearer YOUR_JWT_TOKEN'")
    
    print("\n3. Create a member in a tree (using partition_key):")
    print(f"   curl -X POST {base_url}/trees/TREE_ID/member \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
    print("        -H 'X-Partition-Key: PARTITION_KEY_FROM_STEP_1' \\")
    print("        -d '{")
    print("          \"name\": \"Jane\",")
    print("          \"surname\": \"Doe\",")
    print("          \"gender\": \"female\",")
    print("          \"description\": \"Another member\",")
    print("          \"born\": \"1992-01-01T00:00:00Z\",")
    print("          \"pic\": \"https://example.com/photo.jpg\",")
    print("          \"photos\": \"https://example.com/photos\"")
    print("        }'")
    
    print("\n4. Get members in a tree:")
    print(f"   curl -X GET {base_url}/trees/TREE_ID/members \\")
    print("        -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
    print("        -H 'X-Partition-Key: PARTITION_KEY_FROM_STEP_1'")
    
    print("\n📊 Expected Results:")
    print("   ✅ Tree creation returns partition_key")
    print("   ✅ All operations are scoped to partition")
    print("   ✅ Cross-partition access is denied")
    print("   ✅ User can only access their own trees")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_partitioning_system()
