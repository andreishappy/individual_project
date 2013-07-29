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
package andrei

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

/**
 * Class main() shows how to trigger Java actions from within a rule evaluation.
 * A persistent table named <i>actions</i> defines the actions and has at least the following columns
 * <ol>
 * <li> integer with value 0 or 1 controlling whether the action is called asynchronously(0) or synchronously(1).
 * <li> String containing the name of the method including full class name to be called.
 * </ol>
 * Optionally, the <i>actions</i> table may declare additional columns.  If so then these define the types
 * and values of arguments also passed to the action.  The signature of the action includes the rule engine,
 * tuple state before and after evaluation and the optional arguments from the <i>actions</i> table.
 * <p>
 * static void MyAction(IRuleEngine engine, TupleState beginState, TupleState endState, ...);
 * <p>
 * Primitive types from the <i>actions</i> table are turned into Java objects.  So for example,
 * int becomes Integer and double becomes Double.
 * <p>
 * Usage: java com.ibm.watson.dsm.samples.RuleActionExample.class
 * <p>
 * And should print out something like the following:
 * <pre>
 * Engine 1 topology changes...
 * TupleSet:TupleSetDescriptor: appDesc=RuleTopologyChangeExample/engine1, name=output1, [ColumnDescriptor: name=NODE, type=String, ColumnDescriptor: name=STATUS, type=String, ColumnDescriptor: name=TOC__INTERNAL, type=Timestamp][
 * Tuple[TupleEntry: value=engine2, TupleEntry: value=added, TupleEntry: value=1970-01-01 12:50:23.345]
 * ]
 * Engine 2 topology changes...
 * TupleSet:TupleSetDescriptor: appDesc=RuleTopologyChangeExample/engine2, name=output1, [ColumnDescriptor: name=NODE, type=String, ColumnDescriptor: name=STATUS, type=String, ColumnDescriptor: name=TOC__INTERNAL, type=Timestamp][
 * Tuple[TupleEntry: value=engine1, TupleEntry: value=removed, TupleEntry: value=1970-01-01 12:50:24.409]
 * ]
 * </pre>
 * @author dawood
 *
 */
public class AndreiAction {

    /** 
     * Rules used to demonstrate the use of an action type table. Please note that these are not sophisticated rules
     * and are only to demonstrate the mechanics of action tables
     */
    final static String rules = 
	// An input table that gets copied into the action table.
	"input to_call(int synchronous, char[128] method, char[128] str, int x, double y);\n"
				
	+ "system peers(char[128] node, char[64] relationship);\n"
			
	// This input tuple, if seen, will trigger the setting of the action table with the action2 method.		
	+ "input trigger(int x);\n"
			
	+ "persistent keep(char[128] method);\n"
			
	// The actions table defining the synchronicity of the call, the method to call and its arguments.
	+ "action actions(int synchronous, char[128] method, char[128] str, int x, double y);\n"
			
	// This rule copies the values from to_call into the actions table, effectively calling what is passed in using to_call
			
	+ "keep(m) if actions(s,m,str,x,y);\n"
	+ "actions(s,m,str,x,y) if to_call(s,m,str,x,y);\n"
			
	// This sets values in the actions tables when the trigger tuple is seen.
	+ "actions(1,\"andrei.AndreiAction.action2\",\"Hello\",x,2.0) if  trigger(x);\n"
			
	+ "actions(1,\"andrei.AndreiAction.action3\",\"Hello\",2,2) if  peers(*,Self);\n"

	;
		
    /**
     * Defines one of the methods that can be used as an action in the rules.  The first 3 arguments must be
     * of the types declared here.  The next arguments are defined by the 3rd, 4th,...Nth columns of the actions table.
     * @param engine the engine running the rules that triggered this action.
     * @param begin the value of the tuples in the rules before the evaluation that triggered this action.
     * @param end the value of the tuples in the rules after the evaluation that triggered this action.
     * @param str the value in the action table's <i>str</i> column that triggered this action.
     * @param x the value in the action table's <i>x</i> column that triggered this action.
     * @param y the value in the action table's <i>y</i> column that triggered this action.
     */
    public static void action1(IRuleEngine engine, TupleState begin, TupleState end, String str, Integer x, Double y) {
	System.out.println("action1: str=" + str + ", x=" + x + ", y=" + y);
    }
		
    /** The 2nd action method */
    public static void action2(IRuleEngine engine, TupleState begin, TupleState end, String str, Integer x, Double y) {
	System.out.println("action2: str=" + str + ", x=" + x + ", y=" + y);
    }
    public static void action3(IRuleEngine engine, TupleState begin, TupleState end, String str, Integer x, Double y){
	IReadOnlyTupleStorage state = engine.getReadOnlyTupleStorage();
	System.out.println("STATE OF ENGINE IS \n" + state.toString());
    }
    /**
     * @param args
     * @throws DSMException 
     * @throws IOException 
     */
    public static void main(String[] args) throws DSMException, IOException {

	// Create a descriptor for the name space used by the engine we're creating.  
	IApplicationDescriptor appDesc = new ApplicationDescriptor("RuleActionExample");
			
	// Create the rule engine with the rules above.
	DSMDefinition def = DSMParser.parse(new StringReader(rules));
	DSMEngine dsmEngine = new DSMEngine(appDesc,  def);
		
	// Start engine, otherwise nothing works.
	dsmEngine.start();

	// Load a tuple into to_call which defines the action to call and the values to pass to it.
	String method = "com.ibm.watson.dsm.samples.RuleActionExample.action1";
	ITuple t1 = new Tuple(1, method, "string and values from tuple", 2, 3.0);
	dsmEngine.addTuples("to_call", t1);			// Send in the to_call tuple to the engine, which triggers an evaluation

	// Now load a trigger tuple to set the action2 method to be called.
	t1 = new Tuple(10);
	dsmEngine.addTuples("trigger", t1);		// Send in the trigger tuple to the engine, again triggering an evaluation
			
	// Stop the engine cleanly.
	dsmEngine.stop();
			
    }

}
