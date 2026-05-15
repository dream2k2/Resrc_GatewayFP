ping -c 5 8.8.8.8 &> /dev/null
  if [ "$?" == "0" ] ; then
     echo "Network Active"
  else
     echo "Network Error"

     shutdown -r now
  fi