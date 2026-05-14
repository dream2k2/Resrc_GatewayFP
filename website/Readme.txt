< Scanner Settings Web >

    Web IP : 192.168.3.1:5000


< Develop History >

    ssh-keygen -R 192.168.3.1
    ssh -o "HostKeyAlgorithms ssh-rsa" root@192.168.3.1

    프로그램 위치 : /root/website/

    opkg update
    pip3 install flask
    export FLASK_ENV=development

    chmod -x /root/website/website.sh

    /etc/rc.local 에 (sh /root/website/website.sh)& 추가
    
    ```
        # Put your custom commands here that should be executed once
        # the system init finished. By default this file does nothing.

        (sh /root/website/website.sh)&
        (sh /root/Gateway_swV2/autostart.sh)

        exit 0
    ```

    바로 실행 안되면 이렇게도 해보고...

    chmod +x /etc/rc.local
    chmod 644 /etc/rc.local