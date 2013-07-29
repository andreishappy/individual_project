/*******************************************************************************
 * Copyright IBM Corporation 2013.
 *  
 * GOVERNMENT PURPOSE RIGHTS
 *  
 * Contract No. W911NF-06-3-0002
 * Contractor Name: IBM 
 * Contractor Address:  IBM T. J. Watson Research Center.
 *                      1101 Kitchawan Rd
 *                      Yorktown Heights, NY 10598 
 *  
 *  The Government's rights to use, modify, reproduce, release, perform, display or disclose this software are restricted 
 *  by Article 10 Intellectual Property Rights clause contained in the above identified contract. Any reproductions of the
 *  software or portions thereof marked with this legend must also reproduce the markings.
 *******************************************************************************/
package andrei;

import java.io.IOException;
import java.io.StringReader;

import com.ibm.watson.dsm.DSMException;
import com.ibm.watson.dsm.engine.IRuleEngine;
import com.ibm.watson.dsm.engine.TupleState;
import com.ibm.watson.dsm.engine.app.DSMEngine;
import com.ibm.watson.dsm.engine.parser.dsm.DSMDefinition;
import com.ibm.watson.dsm.engine.parser.dsm.DSMParser;
import com.ibm.watson.dsm.platform.ApplicationDescriptor;
import com.ibm.watson.dsm.platform.IApplicationDescriptor;
import com.ibm.watson.dsm.platform.tuples.IReadOnlyTupleStorage;
import com.ibm.watson.dsm.platform.tuples.ITuple;
import com.ibm.watson.dsm.platform.tuples.Tuple;

public class Tester {

    public static void action1(IRuleEngine engine, TupleState begin, TupleState end, String str, Integer x, Double y) {
	System.out.println("action1: str=" + str + ", x=" + x + ", y=" + y);
    }




}
