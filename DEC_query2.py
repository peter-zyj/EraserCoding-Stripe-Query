__author__ = 'yijunzhu'

import os, sys
import time, datetime, re
import subprocess,optparse
import pexpect

########SSH logon stuff############
default_passwd = "rootroot"
prompt_firstlogin = "Are you sure you want to continue connecting \(yes/no\)\?"
prompt_passwd = "root@.*'s password:"
prompt_logined = "\[root@.*\]#"
prompt_percentage = ".*100%.*"

########Cluster MGMT IP############
#IP_List = ['172.22.125.33',
#           '172.22.125.229',
#           '172.22.125.226',
#           '172.22.125.227',
#	   '172.22.125.224',
#           '172.22.125.225',
#           '172.22.125.16',
#           '172.22.125.48',
#           '172.22.125.49',
#           '172.22.125.52',
#           '172.22.125.211',
#           '172.22.125.210']


IP_List = ['10.74.17.89',
	   '10.74.17.90',
	   '10.74.17.95']	

def SSHClient(IP,prompt=prompt_logined):
    try:
        result = ""
        ssh = pexpect.spawn('ssh root@%s' % IP)
        result = ssh.expect([prompt_firstlogin, prompt_passwd, prompt, pexpect.TIMEOUT],timeout=2000)

        ssh.logfile = None
        if result == 0:
            ssh.sendline('yes')
            ssh.expect(prompt_passwd)
            ssh.sendline(default_passwd)
            ssh.expect(prompt)

        elif result == 1:
            ssh.sendline(default_passwd)
            ssh.expect(prompt)


        elif result == 2:
            pass
        elif result == 3:
            print "Connection::"+"ssh to %s timeout" %IP
            return result
        return ssh
    except:
        print "!!!!!!!!!!!Connection ERROR::",IP
        print "debug::result is ",result
        print 'debug::Mismatch BTW default expect or unexpected things happen!'
        debug = "debug::Connection::"+ssh.before[:-1]
        print debug
        print "~~~~~~~~~~~Connection ERROR::",IP
        return debug
        #sys.exit(0)



def execute(gid):

    gid = gid.replace('0X','').replace('0x','')
    command1 = 'echo 4 >/proc/calypso/tunables/cm_logserverinfo'
    command2 = 'ls -tr /arroyo/log/serverinfo.log* | tail -n 1'

    # Pattern1 = r'(?s)Object 0x%(Goid)s.*?(?=\d+ Object 0x)' % {"Goid":gid}
    # Pattern1 = r'(?s)Object 0x%(Goid)s.*?(?=\d+ Object 0x)|Object 0x%(Goid)s.*?(?=\={9})' % {"Goid":gid}
    # Pattern1 = r'(?s)Object 0x%(Goid)s.*?((?=\d+ Object 0x)|(?=DataRecovery))' % {"Goid":gid}
    Pattern1 = r'(?s)Object 0x%(Goid)s.*?(?=\d+ Object 0x)|Object 0x%(Goid)s.*?(?=DataRecovery)' % {"Goid":gid}

    dict = {}
    dictData = {}
    dictParity = {}

    for i in IP_List:
        ssh = SSHClient(i)
        if type(ssh) == pexpect.spawn:
            ssh.sendline(command2)
            ssh.expect(prompt_logined)
            logFile = ssh.before[:-1].split()[-2]

            ssh.sendline("rm -rf %s" % (logFile))
            ssh.expect(prompt_logined)

            ssh.sendline("echo 1 > /proc/calypso/test/reopen_logfiles")
            ssh.expect(prompt_logined)

            ssh.sendline(command1)
            ssh.expect(prompt_logined)
            time.sleep(5)

            ssh.sendline(command2)
            ssh.expect(prompt_logined)
            logFile = ssh.before[:-1].split()[-2]
            time.sleep(5)

            ssh.sendline("cat %s" % (logFile))
            ssh.expect(prompt_logined)
            content = ssh.before[:-1]

            tar = None
            mode = None
            if gid in content:
                # tar = re.compile(Pattern1).findall(content)[-1]
                List = re.compile(Pattern1).findall(content)
                for stripe in List:
                    keyList = re.compile(r'(?m)^.*StripeNumber.*?\(\d+:\d+\)').findall(stripe)[0].split()
                    tar = stripe.replace("StripeNumber","StripeNumber"+"(%s)"%(i))
                    print "debug::",i
                    print "debug::",keyList
                    if "DATA_STRIPE" in stripe:
                        mode = keyList[-1]
                        indexD = keyList[2]

                        dictData[indexD] = [i,tar]

                    elif "PARITY_STRIPE" in stripe:
                        indexP = keyList[2]
                        dictParity[indexP] = [i,tar]


            ssh.close()

        else:
            print "%(IP)s not connected" % {"IP":i}

    # print dictData
    #
    # print dictParity
    dict["Data"] = dictData
    dict["Parity"] = dictParity

    # print dict

    ##########
    print "DEC Mode::",mode
    print '=================Data Stripe==============='

    num1 = len(dict["Data"].keys())
    for index1 in range(num1):
        print dict["Data"][str(index1)][1]

    print '=================Parity Stripe==============='

    num2 = len(dict["Parity"].keys())
    for index2 in range(num2):
        print dict["Parity"][str(index2)][1]





if __name__ == '__main__':
    usage ="""
example: %prog -g "[Ox]123456"
"""
    parser = optparse.OptionParser(usage)

    parser.add_option("-g", "--GoidID", dest="GID",
                      default='Null',action="store",
                      help="the Input Goid ID specified by user")


    (options, args) = parser.parse_args()

    argc = len(args)
    if argc != 0:
        parser.error("incorrect number of arguments")
        print usage
    else:
        if options.GID != "Null":
            result = execute(options.GID)

        else:
            print usage

