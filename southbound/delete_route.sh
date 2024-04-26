# List and delete routes associated with interfaces starting with 'rs_'
ip route show | grep 'dev rs_' | while read route; do
  sudo ip route del $route
done

