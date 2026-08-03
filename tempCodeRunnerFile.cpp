#include <bits/stdc++.h>
using namespace std;

vector<vector<int>> adj;
vector<long long> a;
vector<long long> subtree;
vector<long long> cost;
long long totalSum = 0;
long long ans = 0;

void dfs1(int v, int parent, long long depth){
    subtree[v] = a[v];
    cost[1] += depth*a[v];

    for(int child : adj[v]){
        if(child == parent){
            continue;
        }
        dfs1(child, v, depth+1);
        subtree[v] += subtree[child];
    }
}

void dfs2(int v, int parent){
    ans = max(ans, cost[v]);
    for(int child : adj[v]){
        if(child == parent){
            continue;
        }
        cost[child] = cost[v]+totalSum-2*subtree[child];
        dfs2(child, v);
    }
}

int main(){
    int n;
    cin>>n;
    a.resize(n+1);
    adj.resize(n+1);
    subtree.resize(n+1);
    cost.resize(n+1);

    for(int i = 1; i <= n; i++){
        cin>>a[i];
        totalSum += a[i];
    }
    for(int i = 0; i < n-1; i++){
        int u, v;
        cin>>u>>v;
        adj[u].push_back(v);
        adj[v].push_back(u);
    }

    ans = cost[1];
    dfs1(1, 0, 0);
    dfs2(1, 0);
    cout<<ans<<endl;
    
    return 0;
}