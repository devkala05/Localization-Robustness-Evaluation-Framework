#include <bits/stdc++.h>
using namespace std;

int main(){
    int t;
    cin>>t;
    while(t--){
        int n;
        cin>>n;
        vector<long long> a(n+1), b(n+1), c(n+1, 0);
        for(int i = 1; i<=n; i++){
            cin>>a[i];
        }
        for(int i = 1; i <= n; i++){
            cin>>b[i];
            c[i] = c[i-1]+b[i];
        }
        vector<long long> d1(n+2, 0);
        vector<long long> d2(n+2, 0);
        for(int i = 1; i <= n; i++){
            long long target = c[i - 1] + a[i];
            int pos = upper_bound(c.begin(), c.end(), target)-c.begin();
            d1[i]++;
            d1[pos]--;
            if(pos<=n){
                d2[pos] += target-c[pos - 1];
            }
        }
        long long active = 0;
        for(int i = 1; i<=n; i++){
            active += d1[i];
            long long ans = active*b[i]+d2[i];
            cout<<ans<<" ";
        }
        cout<<endl;
    }
    return 0;
}