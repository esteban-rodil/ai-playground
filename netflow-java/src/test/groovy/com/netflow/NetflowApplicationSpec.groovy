package com.netflow

import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.context.ApplicationContext
import spock.lang.Specification

@SpringBootTest
class NetflowApplicationSpec extends Specification {

    @Autowired
    ApplicationContext context

    def "application context loads successfully"() {
        expect:
        context != null
    }

    def "NetflowApplication bean is registered"() {
        expect:
        context.containsBean("netflowApplication")
    }
}
